<h1 align="center"><code>anycastd</code></h1>

<div align="center">
  <a href="https://github.com/gecio/anycastd/actions">
    <img src="https://github.com/gecio/anycastd/workflows/CI/badge.svg" alt="CI status">
  </a>
  <a href="https://codecov.io/gh/gecio/anycastd">
    <img src="https://codecov.io/gh/gecio/anycastd/graph/badge.svg?token=DPOGLYZ26N)" alt="code coverage">
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

- [Usage Example](#usage-example)
- [Services](#services)
  - [Prefixes](#prefixes)
    - [FRRouting](#frrouting)
  - [Health Checks](#health-checks)
    - [Cabourotte](#cabourotte)
- [Configuration](#configuration)
  - [Schema](#schema)

## Usage Example

In the following example, we will use `anycastd` to manage the prefixes of two dual-stacked services commonly run on the same host. [FRRouting] is used to announce the prefixes of both services which are health checked through [Cabourotte].

### `anycastd` configuration

To configure the two services in `anycastd`, we create the `/etc/anycastd/config.toml` configuration file with the following contents.

```toml
[services.dns]
prefixes.frrouting = ["2001:db8::b19:bad:53", "203.0.113.53"]
checks.cabourotte = ["dns"]

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

The first service, aptly named "dns", simply configures a DNS resolver service that announces the prefixes `2001:db8::b19:bad:53/128` & `203.0.113.53/32` through [FRRouting] as long as the [Cabourotte] health check `dns` is reported as healthy.

The second service, "ntp" is similar in functionality, although its configuration is a bit more verbose. Rather than omitting values that have a preconfigured default, a [VRF] as well as a health check interval are explicitly specified.

### FRRouting configuration

Next, we need to configure [FRRouting] so that `anycastd` can add and remove prefixes based on the services health checks. To do this, we create the `/etc/frr/frr.conf` with the following minimal configuration.

```
!
router bgp 65536
 bgp router-id 203.0.113.179
 neighbor unnumbered peer-group
 neighbor unnumbered remote-as external
 neighbor unnumbered capability extended-nexthop
 neighbor eth0 interface peer-group unnumbered
 !
 address-family ipv4 unicast
  redistribute static
 !
 address-family ipv6 unicast
  redistribute static
  neighbor fabric activate
  neighbor fabric nexthop-local unchanged
!
router bgp 65537 vrf 123
 bgp router-id 203.0.113.181
 neighbor unnumbered peer-group
 neighbor unnumbered remote-as external
 neighbor unnumbered capability extended-nexthop
 neighbor eth1 interface peer-group unnumbered
 !
 address-family ipv4 unicast
  redistribute static
 !
 address-family ipv6 unicast
  redistribute static
  neighbor fabric activate
  neighbor fabric nexthop-local unchanged
!
```

This creates two BGP instances, `AS65536` in the default [VRF] and `AS65537` in [VRF] `123`.
Both of them have a single unnumbered session that will be used to advertise the service prefixes.
The most important statement here is `redistribute static` for both IPv4 and IPv6, instructing [FRRouting] to redistribute the static routes containing the service prefixes that will later be created by `anycastd`.

### Cabourotte configuration

The last thing we have to configure is [Cabourotte], which performs the actual health checks. We create the following `/etc/cabourotte/config.yml`.

```yaml
---
http:
  host: 127.0.0.1
  port: 9013

dns-checks:
  # Assumes that the DNS service is used as system wide resolver.
  - name: dns
    domain: check.local
    timeout: 1s
    interval: 5s
    expected-ips: ["2001:db8::15:600d"]

command-checks:
  - name: ntp_v6
    timeout: 3s
    interval: 5s
    command: ntpdate
    arguments: ["-q", "2001:db8::123:7e11:713e"]
  - name: ntp_v4
    timeout: 3s
    interval: 5s
    command: ntpdate
    arguments: ["-q", "203.0.113.123"]
```

This sets up two fairly rudimentary health checks. The first renders healthy if a request to the DNS service for the `check.local` name returns the IPv6 address `2001:db8::15:600d` in the form of an `AAAA` record. The other two checks, `ntp_v6` and `ntp_v4` use the `ntpdate` CLI utility to determine if a date is returned by the NTP service.

### Starting services

To finish up, we need to start our services. For this example we assume that both services as well as [Cabourotte] are run using [systemd] while `anycastd` is run directly for the purposes of this example.

So, to start the DNS, NTP and [Cabourotte] services we run

```sh
$ systemctl start dns.service ntp.service cabourotte.service
```

After which we can start `anycastd` itself.

```sh
$ anycastd run
2024-03-25T15:17:23.783539Z [info     ] Reading configuration from /etc/anycastd/config.toml. config_path=/etc/anycastd/config.toml
2024-03-25T15:17:23.785613Z [info     ] Starting service "dns".      service_health_checks=['dns'] service_healthy=False service_name=dns service_prefixes=['2001:db8::b19:bad:53', '203.0.113.53']
2024-03-25T15:17:23.785613Z [info     ] Starting service "ntp".      service_health_checks=['ntp_v4', 'ntp_v6'] service_healthy=False service_name=ntp service_prefixes=['2001:db8::123:7e11:713e', '203.0.113.123']
2024-03-25T15:17:23.797760Z [info     ] Service "dns" is now considered healthy, announcing related prefixes. service_health_checks=['dns'] service_healthy=True service_name=dns service_prefixes=['2001:db8::b19:bad:53', '203.0.113.53']
2024-03-25T15:17:23.812260Z [info     ] Service "ntp" is now considered healthy, announcing related prefixes. service_health_checks=['ntp_v4', 'ntp_v6'] service_healthy=True service_name=ntp service_prefixes=['2001:db8::123:7e11:713e', '203.0.113.123']
```

`anycastd` will execute the health checks and, since all of them pass, announce the configured service IPs, which we can verify by looking at the new [FRRouting] running configuration.

```diff
@@ -7,9 +7,11 @@
  neighbor eth0 interface peer-group unnumbered
  !
  address-family ipv4 unicast
+  network 203.0.113.53/32
   redistribute static
  !
  address-family ipv6 unicast
+  network 2001:db8::b19:bad:53/128
   redistribute static
   neighbor fabric activate
   neighbor fabric nexthop-local unchanged
@@ -22,9 +24,11 @@
  neighbor eth1 interface peer-group unnumbered
  !
  address-family ipv4 unicast
+  network 203.0.113.123/32
   redistribute static
  !
  address-family ipv6 unicast
+  network 2001:db8::123:7e11:713e/128
   redistribute static
   neighbor fabric activate
   neighbor fabric nexthop-local unchanged
```

### Stopping services

`anycastd` will keep prefixes announced as long as health checks pass.
To stop announcing prefixes, even though the underlying services are healthy, for example to perform maintenance,
simply stop `anycastd`, causing all service prefixes to be denounced.

```sh
^C
2024-03-25T15:20:29.738135Z [info     ] Received SIGINT, terminating.
2024-03-25T15:20:29.817023Z [info     ] Service "dns" terminated.    service=dns
2024-03-25T15:20:29.819003Z [info     ] Service "ntp" terminated.    service=ntp
```

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
that interface with commonly used BGP daemons.** Supported BGP daemons along with their configuration options are described below.

---

#### FRRouting

Free Range Routing, [FRRouting], or simply FRR is a free and open source Internet routing protocol suite for Linux and Unix platforms.
Amongst others, it provides a BGP implementation that can be used to announce BGP service prefixes dynamically.

##### Options

| Option                     | Description                                                         | Default          | Examples                                                                 |
| -------------------------- | ------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------ |
| **prefix** <br> (required) | The network prefix to create when healthy.                          | `null`           | `2001:db8:4:387b::/64` <br> `192.0.2.240/28` <br> `2001:db8::b19:bad:53` |
| _vrf_                      | A VRF to create the prefix in. If omitted, the default VRF is used. | `None`           | `EDGE`                                                                   |
| _vtysh_                    | The path to the vtysh binary used to configure FRRouting.           | `/usr/bin/vtysh` | `/usr/local/bin/vtysh`                                                   |

##### Supported Versions

While CI integration tests only target the latest version of FRRouting, we aim to support releases made within the last 6 months at minimum. `anycastd` is known to work with versions starting from `7.3.1`, although older versions are likely to work as well.

### Health Checks

Assessments on individual components constituting the service to ascertain the overall operational status of the service.
A service is considered healthy as a whole if all of its health checks report a healthy status. Possible health check types along with their configuration options are described below.

---

#### Cabourotte

[Cabourotte] is a general purpose healthchecking tool written in Golang that can be configured to execute checks, exposing their results via API.

##### Options

| Option                   | Description                                                           | Default                 | Examples                 |
| ------------------------ | --------------------------------------------------------------------- | ----------------------- | ------------------------ |
| **name** <br> (required) | The name of the health check, as defined in [Cabourotte].             | `null`                  | `anycast-dns`            |
| _url_                    | The base URL of the Cabourotte API.                                   | `http://127.0.0.1:9013` | `https:://healthz.local` |
| _interval_               | The interval in seconds at which the health check should be executed. | `5`                     | `2`                      |

---

## Configuration

`anycastd` can be configured using a TOML configuration file located at `/etc/anycastd/config.toml`, or a path specified through the `--configuration` parameter.
For a quick primer on TOML, see [A Quick Tour of TOML](https://toml.io).

### Schema

```toml
[services] # A definition of services to be managed by `anycastd`.

  [services.<service-name>] # A service with a unique and recognizable name.
    [[prefixes.<prefix-type>]] # A prefix of the specified type.
      # Options related to the specified prefix type.

    [[checks.<check-type>]] # A check of the specified type.
      # Options related to the specified check type.
```

## Contributing

Contributions of all sizes that improve `anycastd` in any way, be it DX/UX, documentation, performance or other are highly appreciated.
To get started, please read the [contribution guidelines](.github/CONTRIBUTING.md). Before starting work on a new feature you would like to contribute that may impact simplicity, reliability or performance, please open an issue first.

[Anycast]: https://en.wikipedia.org/wiki/Anycast
[FRRouting]: https://github.com/FRRouting/frr
[Cabourotte]: https://github.com/appclacks/cabourotte
[VRF]: https://en.wikipedia.org/wiki/Virtual_routing_and_forwarding
[systemd]: https://systemd.io/
