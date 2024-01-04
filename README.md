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

`anycastd` is a daemon that manages services using multiple backends, each announcing the same
service prefixes to the network as a form of load balancing, commonly know as [Anycast].
It can be used to ensure that service prefixes are only announced when the underlying service is actually healthy, avoiding attracting traffic to service instances
that aren't functioning correctly.

## Table of Contents

- [Architecture](#architecture)
  - [Services](#services)
    - [Prefixes](#prefixes)
    - [Health Checks](#health-checks)
- [Configuration](#configuration)

## Architecture

### Services

The main unit of abstraction used within `anycastd`. They combine [prefixes](#prefixes) and [health
checks](#health-checks) to form a logical service unit that executes health checks and manages announcements.

#### High Level Service Logic

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

#### Prefixes

Represents a BGP network prefix that can be announced or denounced as part of a [Service]. \
`anycastd` does not come with its own BGP implementation, but rather aims to provide abstractions
that interface with commonly used BGP daemons.

#### Health Checks

Tests the components that make up a [Service] and reports whether they are healthy or not. A [Service] is considered healthy as a whole if all of it's health checks report a
healthy status.

## Configuration

`anycastd` can be configured using a TOML configuration file located at `/etc/anycastd/config.toml`, or a path specified through the `--configuration` parameter.

A configuration for two dual-stacked services commonly run on the same host, both using [FRRouting] for BGP announcements and running health checks through [Cabourotte] could look like the following:

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

[Anycast]: https://en.wikipedia.org/wiki/Anycast
[Service]: #services
[FRRouting]: https://github.com/FRRouting/frr
[Cabourotte]: https://github.com/appclacks/cabourotte
[VRF]: https://en.wikipedia.org/wiki/Virtual_routing_and_forwarding
