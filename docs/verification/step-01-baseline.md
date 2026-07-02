# Step 1 Verification - Piano e criteri

## Cosa e' stato implementato

Sono stati aggiunti solo file di documentazione:

- `docs/migration-plan.md`
- `docs/verification/step-01-baseline.md`

Questo step non modifica il backend Python, il frontend, gli script di avvio o il
packaging esistente.

## Come verificare

Dal repository:

```bash
git status --short
sed -n '1,220p' docs/migration-plan.md
sed -n '1,160p' docs/verification/step-01-baseline.md
```

Controlli attesi:

- `git status --short` mostra `?? docs/` tra i file non tracciati;
- l'app attuale non e' stata modificata da questo step;
- il piano contiene al massimo dieci step e ogni step ha un criterio di verifica.

## Esito atteso

Se il piano ti sembra corretto, si puo' procedere allo Step 2: creare una
baseline funzionale dell'app Python attuale, cosi' la migrazione Tauri potra'
essere confrontata con output reali.
