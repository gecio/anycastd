<h1 align="center"><code>anycastd</code></h1>

<div align="center">
  <a href="https://github.com/gecio/anycastd/actions">
    <img src="https://github.com/gecio/anycastd/workflows/CI/badge.svg" alt="CI status">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="ruff">
  </a>
  <a href="https://github.com/python/mypy">
    <img src="https://img.shields.io/badge/Types-Mypy-blue.svg" alt="typecheck">
  </a>
  <a>
    <img src="https://img.shields.io/badge/v3.11+-black?style=flat&color=FFFF00&label=Python" alt="python version">
  </a>
  <a href="https://pdm.fming.dev">
    <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm">
  </a>
</div>
<br>

`anycastd` functions as a daemon managing the announcement of network prefixes employed by redundant services using multiple backends that share a common set of service prefixes.
Each prefix is announced individually to the network, forming a load-balancing strategy with redundancy, commonly referred to as Anycast.
This tool ensures that service prefixes are exclusively announced when all underlying service components are confirmed to be in a healthy state.
By doing so, `anycastd` prevents the attraction of traffic to service instances that may be malfunctioning, avoiding service diruption.

## Table of Contents

- [Services](#services)
  - [Prefixes](#prefixes)
  - [Health Checks](#health-checks)
- [Configuration](#configuration)
  - [Example](#example)
  - [Prefixes](#prefixes-1)
    - [FRRouting](#frrouting)
  - [Health Checks](#health-checks-1)
    - [Cabourotte](#cabourotte)
  - [Schema](#schema)

## Services

Services are the main unit of abstraction within `anycastd` and are used to form a logical relationship between health checks and network prefixes containing IP addresses related to the underlying application represented by the service. They work by continuously monitoring defined health checks and announcing/denouncing their prefixes based on
the combination of check results using the logic described below.

```
┌─[Service]─────────────┐                        ┌──────────┐
│                       │                   ┌──> │ HLTH CHK │
│           ┌───────────────────────────────┤    └──────────┘
│ IF healthy•:          │                   │    ┌──────────┐
│     announce prefixes │                   ├──> │ HLTH CHK │
│ ELSE:           •─────────────────────┐   │    └──────────┘
│     denounce prefixes │               │   │    ┌──────────┐
└───────────────────────┘               │   └──> │ HLTH CHK │
                                        │        └──────────┘
                                        │
┌─[Routing Daemon]────────────────┐     │
│ ┌──────────────────────────┐    │     │
│ │ Prefix                   │ <────────┤
│ │ 2001:db8::b19:bad:53/128 │    │     │
│ └──────────────────────────┘    │     │
│ ┌──────────────────────────┐    │     │
│ │ Prefix                   │ <────────┘
│ │ 203.0.113.53/32          │    │
│ └──────────────────────────┘    │
└─────────────────────────────────┘
```

### Prefixes

Represents a BGP network prefix that can be announced or denounced as part of the service.
Typically, these are networks containing "service IPs", meaning the IP addresses exposed by a particular service, serving as the points of contact for clients to make requests while being completely agnostic to the specifics of anycast.

**`anycastd` does not come with its own BGP implementation, but rather aims to provide abstractions
that interface with commonly used BGP daemons.**

### Health Checks

Assessments on individual components constituting the service to ascertain the overall operational status of the service.
A service is considered healthy as a whole if all of its health checks report a healthy status.

## Configuration

`anycastd` can be configured using a TOML configuration file located at `/etc/anycastd/config.toml`, or a path specified through the `--configuration` parameter.

### Example

A configuration for two dual-stacked services commonly run on the same host, both using [FRRouting](#frrouting) for BGP announcements and running health checks through [Cabourotte](#cabourotte) could look like the following:

```toml
[services.dns]
prefixes.frrouting = ["2001:db8::b19:bad:53", "203.0.113.53"]
checks.cabourotte = ["dns_v6", "dns_v4"]

[services.ntp]
prefixes.frrouting = [
    { "prefix" = "2001:db8::123:7e11:713e", "vrf" = "123" },
    { "prefix" = "203.0.113.123", "vrf" = "123" },
]
checks.cabourotte = [
    { "name" = "ntp_v6", "interval" = 1 },
    { "name" = "ntp_v4", "interval" = 1 },
]
```

The first service, aptly named "dns", simply configures a DNS resolver service that announces the prefixes `2001:db8::b19:bad:53/128` & `203.0.113.53/32` through [FRRouting] as long as both [Cabourotte] health checks, `dns_v6` & `dns_v4` are reported as healthy.

The second service, "ntp" is similar in functionality, although it's configuration is a bit more verbose. Rather than omitting values that have a preconfigured default, a [VRF] as well as a health check interval are explicitly specified.

### Prefixes

#### FRRouting

Free Range Routing, [FRRouting], or simply FRR is a free and open source Internet routing protocol suite for Linux and Unix platforms.
Amongst others, it provides a BGP implementation that can be used to announce BGP service prefixes dynamically.

**prefix**

The BGP network prefix to be created if the service is healthy. If no netmask / prefix length is given, a host route is created.\
`2001:db8:4:387b::/64`, `192.0.2.240/28` and `2001:db8::b19:bad:53` would all be valid values, while `2001:db8::b19:bad:53` is equivalent to `2001:db8::b19:bad:53/128`.

_**vrf** (optional)_

A VRF to create the prefix in. If omitted, the default VRF is used.

_**vtysh** (optional)_

The path to the vtysh binary used to configure FRRouting. The default is `/usr/bin/vtysh`.

### Health Checks

#### Cabourotte

[Cabourotte] is a general purpose healthchecking tool written in Golang that can be configured to execute checks, exposing their results via API.

**name**

The name of the health check, as defined in [Cabourotte].

_**url** (optional)_

The base URL of the [Cabourotte] API. `http://127.0.0.1:9013` is used by default.

_**interval** (optional)_

The interval in seconds at which the health check should be executed. The default is `5` seconds.

### Schema

`[services]`

A definition of services to be managed by `anycastd`.

`[services.<service-name>]`

A unique and recognizable name for the service.

`[services.<service-name>.prefixes]`

Prefixes that belong to the service and should be announced when all checks are healthy.

`[services.<service-name>.prefixes.<prefix-type>]`

The type of prefix. See [Prefixes](#prefixes-1) for supported prefix types and their specific options.

`[services.<service-name>.checks]`

Checks that belong to the service and determine whether it is healthy.

`[services.<service-name>.checks.<check-type>]`

The type of health check. See [Health Checks](#health-checks-1) for supported prefix types and their specific options.

[Anycast]: https://en.wikipedia.org/wiki/Anycast
[Service]: #services
[FRRouting]: https://github.com/FRRouting/frr
[Cabourotte]: https://github.com/appclacks/cabourotte
[VRF]: https://en.wikipedia.org/wiki/Virtual_routing_and_forwarding
