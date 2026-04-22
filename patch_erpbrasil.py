"""
patch_erpbrasil.py
Corrige o locale hardcoded no erpbrasil.edoc.pdf 1.2.1.
Executado durante o docker build, após pip install.
"""
import erpbrasil.edoc.pdf.danfe_formata as m
import inspect

f = inspect.getfile(m)
src = open(f).read()

old = "    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')\n"
new = (
    "    for _loc in ['pt_BR.UTF-8', 'pt_BR', 'C.UTF-8', 'C']:\n"
    "        try:\n"
    "            locale.setlocale(locale.LC_ALL, _loc)\n"
    "            break\n"
    "        except locale.Error:\n"
    "            continue\n"
)

if old in src:
    open(f, 'w').write(src.replace(old, new))
    print(f"[OK] Patch erpbrasil aplicado: {f}")
else:
    print(f"[AVISO] Padrao nao encontrado em {f} — erpbrasil pode ter sido atualizado")
    print("Conteudo atual da funcao formata_decimal:")
    for i, line in enumerate(src.split('\n')[13:22], 14):
        print(f"  {i}: {line}")
