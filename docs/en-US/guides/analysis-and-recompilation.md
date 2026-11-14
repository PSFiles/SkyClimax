# Analysis and recompilation guide

End-to-end procedure for going from the retail package to lifted C++. Each step
states whether it has been executed here.

## 1. Extract

```bash
python .vendor/ps3recomp/tools/pkg_extract.py "$SKYCLIMAX_PKG" work/pkg
```

Validated: 46 files.

## 2. Inspect the executable container

```bash
python -m skyclimax self-info work/pkg/USRDIR/EBOOT.BIN --json work/reports/self.json
```

Validated. Expect `retail_encrypted: true`, `entry: 0x4CDF00`, 8 program headers.

## 3. Decrypt

Not executed and not automatable from the package alone.

Required artefact: a PPC64 big-endian `ET_EXEC` ELF. Two acceptable sources:

- a title key supplied by the owner, used with a SELF decryption tool;
- an executable dumped from a running copy of the game.

Record the SHA-256 of the result. If the ELF header does not read
`e_machine = 21` and `e_entry = 0x4CDF00`, the wrong file was decrypted.

## 4. Load

```bash
python .vendor/ps3recomp/tools/ppu_loader.py work/game/EBOOT.elf -o work/meta
```

Validated on a synthetic ELF; expected on the real image:

- non-zero `unique functions` (the OPD table is authoritative);
- a `module TOC (r2)` value;
- a firmware import count in the hundreds.

If `unique functions` is 0, the `.opd` section was not found — the image is
probably stripped or truncated. Stop and fix that before lifting.

## 5. Review the import surface

The import list determines the HLE work. Group it by library and check each
library against the backend's module status. Libraries with no implementation
must be written before the title can boot; this is the main scope driver.

## 6. Lift

```bash
python .vendor/ps3recomp/tools/ppu_lifter.py work/game/EBOOT.elf -o generated/ \
  --functions work/meta/EBOOT.functions.json \
  --imports work/meta/EBOOT.imports.json
```

Validated on a synthetic ELF (1 function → 1,117 lines). On the real image this
is expected to take minutes and to emit thousands of functions across many
chunks.

Sanity checks after lifting:

- function count in the generated sources equals the loader's count;
- no `WARNING: ... has no continuation` lines (each one is a mis-sized
  function range);
- the generated tree compiles.

## 7. Analyse in Ghidra

```bash
export JAVA_HOME="$(pwd)/.tools/jdk25/jdk-25.0.5+8"
.tools/ghidra/ghidra_12.2_PUBLIC/support/analyzeHeadless work/ghidra_proj skyclimax \
  -import work/game/EBOOT.elf -processor "PowerPC:BE:64:default"
```

Validated with a synthetic ELF (import succeeded, correct language selected).

Use Ghidra for what the lifter does not give you: naming functions, recovering
structures, and answering "what does this pointer point at". Keep the names in a
JSON file and feed them back through the lifter's `--names` option so the
generated code stays readable.

## 8. Handle unsupported constructs

When the lifter meets an instruction or pattern it cannot express:

1. Note the guest address and the mnemonic.
2. Decide whether it needs a lifter change (upstream) or an HLE shim (here).
3. If it needs a lifter change, write a patch under `tools/patches/` and record
   it in the decision log.
4. Add a regression case to `tools/regress/` so the construct stays covered.

Never patch generated C++ by hand: it is regenerated on every lift.

## 9. Validate a lift

A lift is correct when the generated function produces the same architectural
state as the guest function. Practical checks, cheapest first:

- the function's return value for a fixed input;
- the guest memory it writes, compared against a reference run;
- a trace of the syscalls it makes, compared against the reference.

"Compiles" is not validation.

## 10. Common failure modes

| Symptom | Likely cause |
|---|---|
| generated function returns immediately | function range ended early; check for `has no continuation` warnings |
| crash inside `ps3_indirect_call` | guest function pointer was not OPD-resolved |
| HLE call returns success but nothing happens | stub implemented as a no-op |
| wrong floating-point results | paired-single or fused-multiply-add semantics |
| hang in a loop | guest condition depends on an unimplemented syscall |
