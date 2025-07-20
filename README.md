# PyStitch

_Interactively labeling needles for OpenQA._

---

## 🚀 One-Key Start

```bash
git clone git@github.com:KangweiZhu/pystitch.git
cd pystitch
./utils/kdelinux_qa_bootstrap --latest
```

## Test the installed system
```bash
qemu-system-x86_64 \
    -enable-kvm \
    -m 4G \
    -cpu host \
    -drive file=$PWD/full_system_testbed.qcow2,format=qcow2 \
    -bios /usr/share/OVMF/x64/OVMF.4m.fd \
    -device VGA,edid=on,xres=1024,yres=768 \
    -serial stdio \
    -vnc :1 \
    -display sdl \
    -qmp unix:/tmp/qmp-kde.sock,server,nowait
```