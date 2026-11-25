alter table public.productos
  add column if not exists activo boolean not null default true;

grant select, insert, update
on table public.productos
to campo_pos;

drop policy if exists campo_pos_insert_productos
on public.productos;

create policy campo_pos_insert_productos
on public.productos
for insert
to campo_pos
with check (true);

drop policy if exists campo_pos_update_productos
on public.productos;

create policy campo_pos_update_productos
on public.productos
for update
to campo_pos
using (true)
with check (true);
