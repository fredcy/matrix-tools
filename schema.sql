create table events (
       event_id	text,
       ts timestamp,
       sender text,
       content jsonb,
       "type" text,
       room_id text
);

alter table only events add constraint events_pkey primary key (event_id);

alter table events owner to matrixlog;
