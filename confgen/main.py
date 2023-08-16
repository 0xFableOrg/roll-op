from pathlib import Path


def generate(datadir: str, layer1: bool):
    print("Creating layer2 directory if not exists")
    layer2_dir = Path(f"{datadir}/layer2")
    layer2_dir.mkdir(parents=True, exist_ok=True)
    layer1_dir = None
    if layer1:
        print("Creating layer1 directory if not exists")
        layer1_dir = Path(f"{datadir}/layer1")
        layer1_dir.mkdir(exist_ok=True)
