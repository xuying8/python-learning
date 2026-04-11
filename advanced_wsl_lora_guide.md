# Advanced WSL Usage + LoRA Fine-Tuning Fundamentals

This guide is designed for engineers who build local AI/dev environments on Windows and need practical LoRA fine-tuning patterns for LLM workflows.

---

## Part 1 — Advanced WSL Guide

## 1) WSL Architecture (WSL1 vs WSL2)

### WSL1
- Translation layer maps Linux syscalls to Windows NT kernel behavior.
- Fast access to Windows files (`/mnt/c/...`) because no VM boundary.
- No real Linux kernel features (limited kernel-level compatibility).

### WSL2
- Lightweight VM with a real Linux kernel.
- Better compatibility for Docker, kernel modules, container runtimes, eBPF-related tooling.
- Separate virtual disk (`ext4.vhdx`) gives better Linux-native I/O.

### Practical decision rule
- Choose **WSL2** for containerized development, ML, and anything requiring modern Linux behavior.
- Keep WSL1 only for niche workflows that require very fast `/mnt` access and no Docker/kernel features.

### Commands
```bash
wsl --status
wsl -l -v
wsl --set-version Ubuntu-22.04 2
```

### Common pitfalls
- Assuming WSL1/WSL2 differ only in speed; they differ in kernel compatibility.
- Running Docker workflows on WSL1 and troubleshooting failures that are architecture-related.

---

## 2) File System Performance Differences (`/mnt` vs native Linux)

### Core behavior
- Accessing files under `/mnt/c` crosses Windows↔Linux boundary and is slower for metadata-heavy workloads.
- Native Linux path (`~/project` inside ext4.vhdx) is much faster for `git`, package managers, and build systems.

### Practical rule
- Store source code and data pipelines in Linux filesystem:
  - Good: `~/src/myapp`
  - Avoid for intensive dev loops: `/mnt/c/Users/.../myapp`

### Real-world scenario
Python monorepo with 60k files:
- `pip install -e .`, `pytest`, `git status` can be several times slower on `/mnt/c`.
- Moving repo to `~/src` usually removes most I/O bottlenecks.

### Commands
```bash
# quick ad-hoc benchmark
time git status
hyperfine 'python -c "import os; [os.stat(p) for p in os.listdir()]"'
```

### Pitfalls
- Editing files from Windows tools + Linux tools concurrently in very large repos can trigger file watcher instability.
- Using antivirus scanning aggressively on mounted paths can degrade dev performance.

---

## 3) Networking and Port Forwarding

### Basics
- WSL2 uses virtualized networking; localhost forwarding generally works from Windows to WSL services.
- Inbound LAN access to WSL service may need explicit `netsh interface portproxy` or firewall rules.

### Commands
```powershell
# Windows PowerShell: view WSL IP
wsl hostname -I

# Example: forward host 0.0.0.0:8080 -> WSL_IP:8080
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=<WSL_IP>

# Open firewall port
netsh advfirewall firewall add rule name="WSL 8080" dir=in action=allow protocol=TCP localport=8080
```

### Real-world scenario
- Serving FastAPI in WSL (`uvicorn app:app --host 0.0.0.0 --port 8000`) for mobile-device testing on same LAN.

### Pitfalls
- WSL IP changes across restart; static forwarding scripts should refresh target IP.
- Binding only to `127.0.0.1` prevents external device access.

---

## 4) Running Docker inside WSL

### Recommended pattern
- Install **Docker Desktop with WSL integration enabled** for your distro.
- Keep Docker data and bind mounts in Linux filesystem.

### Commands
```bash
# in WSL
docker version
docker info

docker run --rm hello-world
```

### Without Docker Desktop (advanced)
- Run `dockerd` inside WSL distro (more manual ops).
- Requires proper cgroup/systemd setup and lifecycle management.

### Pitfalls
- Mounting `/mnt/c/...` into containers can heavily degrade build/runtime performance.
- Confusing Windows Docker context with WSL context; verify `docker context ls`.

---

## 5) GPU Acceleration (CUDA in WSL)

### Requirements
- Windows NVIDIA driver with WSL CUDA support.
- WSL2 distro + compatible CUDA toolkit/libs.

### Validation
```bash
nvidia-smi
python - <<'PY'
import torch
print('cuda available:', torch.cuda.is_available())
print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')
PY
```

### Real-world scenario
- Fine-tuning 7B model adapters in WSL2 with CUDA + bitsandbytes avoids dual-boot and keeps Windows desktop workflow.

### Pitfalls
- Installing conflicting CUDA versions from mixed package sources.
- Assuming GPU pass-through works on WSL1.

---

## 6) Multi-Distribution Management

### Use cases
- Separate distros for stable prod-like environment and experimental ML stack.
- Isolated Python/toolchain versions by distro.

### Commands
```bash
wsl -l -v
wsl --install -d Ubuntu-24.04
wsl --set-default Ubuntu-24.04
wsl --terminate Ubuntu-22.04
wsl --export Ubuntu-24.04 ubuntu2404.tar
wsl --import Ubuntu-24.04-clone D:\wsl\ubuntu2404-clone ubuntu2404.tar
```

### Pitfalls
- Forgetting which distro is default for `wsl` command.
- Large duplicate VHD usage if cloning frequently without cleanup.

---

## 7) `systemd` Usage

### Why it matters
- Enables service managers and tools requiring systemd (`snapd`, `microk8s`, background daemons).

### Enable in `/etc/wsl.conf`
```ini
[boot]
systemd=true
```

Then restart from PowerShell:
```powershell
wsl --shutdown
wsl
```

### Verification
```bash
systemctl is-system-running
systemctl status
```

### Pitfalls
- Forgetting full `wsl --shutdown` after config changes.
- Enabling too many startup services causing slow shell startup.

---

## 8) Performance Tuning Tips

1. Keep hot code/data on Linux filesystem (`~/...`).
2. Use WSL2 + recent kernel (`wsl --update`).
3. Limit unnecessary background services in distro.
4. Tune `.wslconfig` for memory/CPU when running heavy ML + Docker.
5. Periodically compact/cleanup virtual disk if usage balloons.

### Example `.wslconfig` (Windows user profile)
```ini
[wsl2]
memory=16GB
processors=8
swap=8GB
localhostForwarding=true
```

### Pitfalls
- Over-allocating memory starves host OS.
- No swap causes OOM during model training.

---

## Part 2 — LoRA Fine-Tuning Fundamentals

## 1) What is LoRA?

LoRA (Low-Rank Adaptation) fine-tunes large models by freezing original weights and training small low-rank matrices injected into selected layers.

Instead of updating full weight matrix \(W\), LoRA learns a low-rank update \(\Delta W\):

\[
W' = W + \Delta W, \quad \Delta W = BA
\]

- \(A \in \mathbb{R}^{r \times d_{in}}\)
- \(B \in \mathbb{R}^{d_{out} \times r}\)
- rank \(r\) is small (e.g., 8, 16, 32)

This cuts trainable params dramatically while retaining strong task adaptation.

---

## 2) How LoRA Works (ΔW = BA)

For a linear layer output:
\[
y = Wx
\]
LoRA modifies it to:
\[
y = Wx + s \cdot BAx
\]
where \(s = \alpha / r\) is scaling.

### Engineering interpretation
- `W` stays frozen (no optimizer state for full model weights).
- Train only `A`, `B` for target modules.
- Save small adapter checkpoints (`adapter_model.safetensors`) rather than full base model.

---

## 3) Why LoRA is Efficient

### Memory
- Fewer trainable params → lower optimizer state memory.
- Works with 4-bit quantized base model (QLoRA) for major VRAM savings.

### Compute
- Backprop only through adapter params.
- Enables fine-tuning on commodity single-GPU setups.

### Deployment
- Base model reused across tasks.
- Ship tiny adapters per task/domain.

---

## 4) Key Hyperparameters

## rank (`r`)
- Capacity of adapter update.
- Typical range: `4–64`.
- Too low: underfit. Too high: overfit/memory increase.

## alpha
- Scaling factor for adapter contribution.
- Common heuristic: `alpha = 2*r` or `alpha = r`.

## learning rate
- LoRA often uses higher LR than full fine-tuning.
- Typical: `1e-4` to `3e-4` (task/model dependent).

## Additional practical knobs
- `lora_dropout` (e.g., 0.05)
- `target_modules` (scope of adaptation)
- `gradient_accumulation_steps` for effective batch size

---

## 5) Target Modules (Q, K, V, MLP)

Common targets in transformer blocks:
- Attention projections: `q_proj`, `k_proj`, `v_proj`, `o_proj`
- MLP projections: `up_proj`, `down_proj`, `gate_proj`

### Practical recommendations
- Start with `q_proj`, `v_proj` for smaller adapters.
- Add MLP modules when task requires deeper adaptation.
- Validate module names from model architecture before training.

---

## 6) Dataset Format Example (Instruction Tuning)

JSONL example:
```json
{"instruction":"Summarize incident report","input":"Service latency rose to 1.8s after deploy.","output":"Latency increased post-deploy; rollback and profile DB calls."}
{"instruction":"Classify ticket severity","input":"Checkout failing for all users","output":"SEV-1"}
```

Prompt construction (simple):
```python
def format_example(ex):
    return (
        f"### Instruction:\n{ex['instruction']}\n\n"
        f"### Input:\n{ex['input']}\n\n"
        f"### Response:\n{ex['output']}"
    )
```

---

## 7) Training Pipeline with HuggingFace PEFT

```python
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType

model_name = "meta-llama/Llama-2-7b-hf"  # example
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base_model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],
    bias="none"
)

model = get_peft_model(base_model, peft_config)
model.print_trainable_parameters()

dataset = load_dataset("json", data_files={"train": "train.jsonl"})

def preprocess(batch):
    texts = [format_example(x) for x in batch["train"]]
    return tokenizer(texts, truncation=True, max_length=1024)

# For production, use map with batched tokenization and proper labels

args = TrainingArguments(
    output_dir="./lora-out",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    num_train_epochs=3,
    logging_steps=10,
    save_steps=200,
    bf16=True,
    optim="adamw_torch",
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=dataset["train"],
    data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
)

trainer.train()
model.save_pretrained("./lora-adapter")
tokenizer.save_pretrained("./lora-adapter")
```

> Note: production pipelines should implement deterministic preprocessing, masking strategy, validation split, and checkpoint resume policy.

---

## 8) QLoRA Explanation

QLoRA combines:
1. **4-bit quantized base model** (NF4/FP4 via bitsandbytes)
2. **LoRA adapters in higher precision** (fp16/bf16)

Benefits:
- Significant VRAM reduction while preserving useful adaptation quality.
- Makes 7B/13B-scale adapter training feasible on smaller GPUs.

Typical setup:
- `load_in_4bit=True`
- `bnb_4bit_compute_dtype=torch.bfloat16`
- PEFT LoRA config on top.

---

## 9) Inference: Merge vs Adapter

## Adapter mode (recommended for flexibility)
- Load base model + adapter at runtime.
- Pros: tiny artifacts, multi-task switching.
- Cons: slight runtime complexity.

## Merged mode
- Merge adapter weights into base model and export single model.
- Pros: simpler serving artifact.
- Cons: larger storage per task; less modular.

Example (merge):
```python
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(model_name)
model = PeftModel.from_pretrained(base, "./lora-adapter")
merged = model.merge_and_unload()
merged.save_pretrained("./merged-model")
```

---

## 10) Common Mistakes

1. Training on badly formatted instruction data (response leakage, inconsistent templates).
2. Wrong `target_modules` names for the specific architecture.
3. Too high learning rate causing unstable loss spikes.
4. Ignoring eval set and overfitting adapters to synthetic data.
5. Mixing quantization, dtype, and optimizer settings incompatibly.
6. Storing datasets on slow mounted paths in WSL, causing underutilized GPU.

---

## Production Checklist

- [ ] Base model license and usage constraints verified.
- [ ] Dataset quality/PII checks completed.
- [ ] Training reproducibility (seed, config snapshot, package versions).
- [ ] Adapter evaluation with task-specific metrics.
- [ ] Inference path decided: adapter vs merged.
- [ ] WSL environment documented (`wsl --status`, driver/CUDA versions).

