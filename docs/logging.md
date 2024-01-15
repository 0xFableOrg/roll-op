# Logging Policy

The default logging policy for services (process that are supposed to keep running) is to rotate the
logs once they reach 3M in size. This can be configured via the `logrotate_max_size` option (takes a
number followed by a `k`/`M`/`G` suffix).

The logs are rotated up to 300 times (accounted separately per log file) before the oldest rotations
are removed. Rotations older than 14 days are also removed. This can be configured via the
`logrotate_count` and `logrotate_max_days` options.

Finally, you can override settings for individual log files. This is done by specifying logrotate
commands directly (cf. [manpage]). Here's an example of how you can do this:

```toml
# at BOTTOM of the file
[logrotate_overrides]
"l1_node.log" = [
    "size 1M",
    "rotate 10",
]
"l2_node.log" = [
    "size 300k",
    "nocompress",
]
```

[manpage]: https://linux.die.net/man/8/logrotate