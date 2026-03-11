Documentation pour intégrer une nouvelle application.
```markdown
# Intégration d’une application cliente
## 1. Enregistrement
Obtenez un `app_id` en appelant l’API ou en exécutant :
```sql
INSERT INTO ttu_core.registry (app_name) VALUES ('ma_super_app') RETURNING
app_id;
```

## 2. Insertion des données
Au lieu d’écrire directement dans votre table, insérez dans le vault :
```sql
INSERT INTO ttu_core.dissipation_vault (app_id, target_table, payload)
VALUES ('votre-app-id', 'ma_table_finale', '{"data": "valeur"}'::jsonb);