# Testing

This document includes some rambling notes on how to test that everything is working properly.

To test the repo on a completely virgin environment, we can use docker:

```
docker pull ubuntu
docker run -ti --rm --platform linux/arm64 ubuntu /bin/bash
```

Note: `-ti` means interactive and keep stdout attched, `--rm` means removes the container after
it stops.

Can be linux/amd64 for those who have this architecture (I have a M1 Mac).

Inside the container:

```
apt update && apt install python3-pip git build-essential curl
```

You can also `apt install python3-pip git` first, clone the repo (see below) then check
if the scripts gives proper warnings for the missing `make` and `curl`.

(It should also warn for missing `git`, but we can't get the repo without `git` ...)

```
git clone https://github.com/0xFableOrg/simple-op-stack-rollup.git rollop
cd rollop
./rollop setup --yes
./rollop devnet
```

The `--yes` option auto installs all dependencies, you can try without to check that the dialog
works.

Let the devnet run for a while and then check the logs. You can leave the devnet running and open
another terminal by running `docker exec -ti <container-id> /bin/bash`. The container ID will
appear as the hostname in your existing terminal (`root@<container-id>:/#` in front of your
commands).

The hallmark of a successfully running op-stack rollup is that the proposer is able to post output
roots to the L1 chain. You can check with

```
cat deployments/rollup/logs/l2_proposer.log | grep "successfully published"
```

(Substitute `rollup` for your actual deployment name, `rollup` being the default name.)

Then you can run this command, which should be completely equivalent to the first, except the
deployment outputs will be put in `deployments/test` instead of `deployments/rollup`:

```
./rollop --clean --name=test --preset=dev --config=config.toml.example devnet
```

Note that `--clean` is crucial here, as it nukes the previous L1/L2 databases.