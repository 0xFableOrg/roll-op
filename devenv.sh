#!/usr/bin/env bash

# Description: This script is used to setup the development environment for the project.


check_python_version() {
    # Check python version if greater or equal than 3.10, otherwise exit
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c "import sys; sys.exit(not (sys.version_info >= (3, 10)))"; then
        echo "Python version is $python_version"
        return 0
    else
        echo "Python version is $python_version, but 3.10 or greater is required"
        return 1
    fi
}

activate_venv() {
    # Check if venv directory exists, otherwise create it. Then activate venv
    if [ -d "venv" ]; then
        echo "venv directory exists"
    else
        echo "venv directory does not exist, creating it now"
        python3 -m venv venv
    fi
    echo "activating venv"
    source ./venv/bin/activate
}

install_dev_dependencies() {
    # Check if pip3 version is greater or equal than 21.2.1, otherwise upgrade it
    pip3_version=$(python3 -c "import pip; print(pip.__version__)")

    check_pip3_version() {
        python3 -c \
        "import pip;\
        import sys;\
        sys.exit(not [int(x) for x in pip.__version__.split('.')] >= [21, 2, 1])"
    }

    if check_pip3_version; then
        echo "pip3 version is $pip3_version"
    else
        echo "pip3 version is $pip3_version, but 21.2.1 or greater is required"
        pip3 install --upgrade pip
    fi

    # Check if ruff 0.3.2 is installed, otherwise install this version
    ruff_version=$(pip3 freeze | grep ruff | awk -F'==' '{print $2}')
    if [ "$ruff_version" = "0.3.2" ]; then
        echo "ruff version is $ruff_version"
    else
        echo "ruff version is $ruff_version, but 0.3.2 is required"
        pip3 install ruff==0.3.2
    fi

    # Check if autopep8 is installed, otherwise install it
    autopep8_version=2.0.4
    if ! command -v autopep8 &> /dev/null; then
        echo "autopep8 could not be found, installing it now"
        pip3 install autopep8==$autopep8_version
    elif [ "$(autopep8 --version | awk '{print $2}')" != $autopep8_version ]; then
        echo "forcing autopep8 to right version"
        pip3 install autopep8==$autopep8_version
    else
        echo "autopep8 version $autopep8_version"
    fi

    # Check if rust-just==1.36.0 is installed, otherwise install it
    just_version=$(just --version | awk '{print $2}')
    if [ "$just_version" = "1.36.0" ]; then
        echo "just version is $just_version"
    else
        echo "just version is $just_version, but 1.36.0 is required"
        pip3 install rust-just==1.36.0
    fi
}

if check_python_version; then
    activate_venv
    install_dev_dependencies
fi
