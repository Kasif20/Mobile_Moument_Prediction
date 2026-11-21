export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

getprop ro.build.version.sdk

export ANDROID_API_LEVEL = 31

uv pip install --python-platform aarch64-linux-android target/wheels/*.whl
