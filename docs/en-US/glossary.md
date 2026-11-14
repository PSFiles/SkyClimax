# Glossary

Bilingual terminology for the SkyClimax project. The pt-BR column is the only
accepted translation; use it consistently in every document.

| Term (en-US) | Termo (pt-BR) | Meaning |
|---|---|---|
| static recompilation | recompilação estática | Translating guest machine code to host source ahead of time, with no runtime instruction interpretation. |
| lifter | liftedor | The component that translates a single guest function into host source code. |
| lifting | elevação de código | The act of producing host source from guest instructions. |
| guest | convidado | The emulated or recompiled platform (here: PlayStation 3). |
| host | hospedeiro | The machine that runs the result (here: Windows x64). |
| PPU | PPU | PowerPC Processing Unit, the Cell's main general-purpose core. |
| SPU | SPU | Synergistic Processing Unit, the Cell's vector coprocessor. |
| syscall | syscall | A call from guest code into the guest kernel (`sc` instruction). |
| stub | stub | A host function that stands in for a guest library entry point. |
| HLE | HLE | High-level emulation: implementing a guest library natively instead of running its original code. |
| NID | NID | 32-bit identifier the PS3 uses to name an exported library function. |
| PRX | PRX | PS3 relocatable module (shared library) format. |
| SELF | SELF | Signed ELF container used for retail executables. |
| EDAT | EDAT | Encrypted data container used for some game payloads. |
| OPD | OPD | Official Procedure Descriptor: an 8-byte `{code, TOC}` pair used as a function pointer. |
| TOC | TOC | Table of contents pointer kept in `r2` for the 32-bit ABI. |
| PKG | PKG | PlayStation package container that holds the store download. |
| PSARC | PSARC | Sony archive format used by `rom.psarc`. |
| FARC | FARC | Sega archive format used by `SYSTEM.farc` and `shader_cg.farc`. |
| ADX | ADX | CRI Middleware audio stream format. |
| Cg | Cg | NVIDIA shading language; the PS3 build ships compiled `.vp`/`.fp` programs. |
| RSX | RSX | The PS3 GPU and its command interface. |
| milestone | marco | A verifiable checkpoint in the roadmap. |
| planned | planejado | Designed but not written yet. |
| implemented | implementado | Written and present in the repository. |
| validated | validado | Exercised with a recorded command and a recorded result. |
| parity | paridade | The en-US and pt-BR documents carry the same content and structure. |
