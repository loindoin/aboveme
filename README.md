
# aerofade/aboveme

# Introduction

A hacky script to grab planes flying overhead (via Flight Radar) and submit them to mqtt so that i can use the data in tools like home assistant.

Inspired by the following project:

https://github.com/smartbutnot/flightportal

I've also included a helm chart here for the docker image:

https://github.com/aerofade/aboveme-helm-chart



## Contributing

If you find this image useful here's how you can help:

- Send a pull request with your awesome features and bug fixes
- Help users resolve their [issues](../../issues?q=is%3Aopen+is%3Aissue).

## Issues

None known

# Getting started

## Installation

```bash
docker pull aerofade/aboveme:latest
```

## Configuration

Edit the config file here: '/app/config/config.cfg'

## Usage

You can run in docker manually and provide the config.cfg manually - but here is a helm chart to make deployment easier:

https://github.com/aerofade/aboveme-helm-chart
