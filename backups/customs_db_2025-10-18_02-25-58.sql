--
-- PostgreSQL database dump
--

\restrict zWFIalHuiVXtzPoq2jTmbftnzVPEDl9pWiHOjy4OyBrPkbiUV7a8eRLA2J1yuI4

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: correctiontype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.correctiontype AS ENUM (
    'TYPO',
    'WRONG_EXTRACTION',
    'WRONG_HS_CODE',
    'VALIDATION_FIX',
    'OTHER'
);


ALTER TYPE public.correctiontype OWNER TO postgres;

--
-- Name: declarationstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.declarationstatus AS ENUM (
    'UPLOADED',
    'PROCESSING',
    'VALIDATING',
    'READY_FOR_REVIEW',
    'APPROVED',
    'REJECTED',
    'FAILED'
);


ALTER TYPE public.declarationstatus OWNER TO postgres;

--
-- Name: knowledgebasestatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.knowledgebasestatus AS ENUM (
    'ACTIVE',
    'ARCHIVED'
);


ALTER TYPE public.knowledgebasestatus OWNER TO postgres;

--
-- Name: knowledgebasetype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.knowledgebasetype AS ENUM (
    'GOOD_LIST',
    'TARIFF'
);


ALTER TYPE public.knowledgebasetype OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'processor',
    'admin'
);


ALTER TYPE public.userrole OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: corrections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.corrections (
    id uuid NOT NULL,
    declaration_id uuid NOT NULL,
    field_name character varying(255) NOT NULL,
    original_value text,
    corrected_value text NOT NULL,
    original_confidence numeric(3,2),
    correction_type public.correctiontype NOT NULL,
    source_document character varying(50),
    extra_metadata jsonb,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.corrections OWNER TO postgres;

--
-- Name: declarations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.declarations (
    id uuid NOT NULL,
    status public.declarationstatus NOT NULL,
    uploaded_files jsonb,
    extracted_data jsonb,
    draft_data jsonb,
    validation_warnings jsonb,
    confidence_scores jsonb,
    processing_progress double precision,
    processing_error text,
    approved_by_user_id uuid,
    approved_at timestamp with time zone,
    organization_id uuid NOT NULL,
    created_by_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.declarations OWNER TO postgres;

--
-- Name: good_list_entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.good_list_entries (
    id uuid NOT NULL,
    product_description text NOT NULL,
    hs_code character varying(8) NOT NULL,
    price_usd numeric(12,2) NOT NULL,
    weight_kg numeric(10,3) NOT NULL,
    supplier character varying(255),
    extra_metadata jsonb,
    version_id uuid NOT NULL,
    is_active boolean NOT NULL,
    organization_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.good_list_entries OWNER TO postgres;

--
-- Name: knowledge_base_versions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knowledge_base_versions (
    id uuid NOT NULL,
    type public.knowledgebasetype NOT NULL,
    version_number integer NOT NULL,
    record_count integer NOT NULL,
    file_path character varying(500) NOT NULL,
    status public.knowledgebasestatus NOT NULL,
    rollback_reason text,
    uploaded_by_user_id uuid NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now() NOT NULL,
    organization_id uuid NOT NULL
);


ALTER TABLE public.knowledge_base_versions OWNER TO postgres;

--
-- Name: organizations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.organizations (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.organizations OWNER TO postgres;

--
-- Name: tariff_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tariff_rates (
    id uuid NOT NULL,
    hs_code character varying(8) NOT NULL,
    vat_rate numeric(5,4) NOT NULL,
    import_duty_rate numeric(5,4) NOT NULL,
    trade_agreement character varying(50),
    description_vi text,
    description_en text,
    effective_date date NOT NULL,
    version_id uuid NOT NULL,
    is_active boolean NOT NULL,
    organization_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.tariff_rates OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    role public.userrole NOT NULL,
    is_active boolean NOT NULL,
    organization_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
e3061fd0812f
\.


--
-- Data for Name: corrections; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.corrections (id, declaration_id, field_name, original_value, corrected_value, original_confidence, correction_type, source_document, extra_metadata, user_id, created_at) FROM stdin;
\.


--
-- Data for Name: declarations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.declarations (id, status, uploaded_files, extracted_data, draft_data, validation_warnings, confidence_scores, processing_progress, processing_error, approved_by_user_id, approved_at, organization_id, created_by_user_id, created_at, updated_at, deleted_at) FROM stdin;
\.


--
-- Data for Name: good_list_entries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.good_list_entries (id, product_description, hs_code, price_usd, weight_kg, supplier, extra_metadata, version_id, is_active, organization_id, created_at) FROM stdin;
\.


--
-- Data for Name: knowledge_base_versions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.knowledge_base_versions (id, type, version_number, record_count, file_path, status, rollback_reason, uploaded_by_user_id, uploaded_at, organization_id) FROM stdin;
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.organizations (id, name, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tariff_rates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tariff_rates (id, hs_code, vat_rate, import_duty_rate, trade_agreement, description_vi, description_en, effective_date, version_id, is_active, organization_id, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, full_name, role, is_active, organization_id, created_at, updated_at) FROM stdin;
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: corrections corrections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.corrections
    ADD CONSTRAINT corrections_pkey PRIMARY KEY (id);


--
-- Name: declarations declarations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.declarations
    ADD CONSTRAINT declarations_pkey PRIMARY KEY (id);


--
-- Name: good_list_entries good_list_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.good_list_entries
    ADD CONSTRAINT good_list_entries_pkey PRIMARY KEY (id);


--
-- Name: knowledge_base_versions knowledge_base_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_base_versions
    ADD CONSTRAINT knowledge_base_versions_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: tariff_rates tariff_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tariff_rates
    ADD CONSTRAINT tariff_rates_pkey PRIMARY KEY (id);


--
-- Name: knowledge_base_versions uq_knowledge_base_version; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_base_versions
    ADD CONSTRAINT uq_knowledge_base_version UNIQUE (organization_id, type, version_number);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_declarations_draft_data; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_declarations_draft_data ON public.declarations USING gin (draft_data);


--
-- Name: idx_goodlist_description_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_goodlist_description_trgm ON public.good_list_entries USING gin (product_description public.gin_trgm_ops);


--
-- Name: ix_corrections_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_corrections_created_at ON public.corrections USING btree (created_at);


--
-- Name: ix_corrections_declaration_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_corrections_declaration_id ON public.corrections USING btree (declaration_id);


--
-- Name: ix_corrections_field_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_corrections_field_name ON public.corrections USING btree (field_name);


--
-- Name: ix_declarations_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_declarations_created_at ON public.declarations USING btree (created_at);


--
-- Name: ix_declarations_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_declarations_organization_id ON public.declarations USING btree (organization_id);


--
-- Name: ix_declarations_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_declarations_status ON public.declarations USING btree (status);


--
-- Name: ix_good_list_entries_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_good_list_entries_organization_id ON public.good_list_entries USING btree (organization_id);


--
-- Name: ix_good_list_entries_version_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_good_list_entries_version_id ON public.good_list_entries USING btree (version_id);


--
-- Name: ix_knowledge_base_versions_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_knowledge_base_versions_organization_id ON public.knowledge_base_versions USING btree (organization_id);


--
-- Name: ix_tariff_rates_hs_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tariff_rates_hs_code ON public.tariff_rates USING btree (hs_code);


--
-- Name: ix_tariff_rates_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tariff_rates_is_active ON public.tariff_rates USING btree (is_active);


--
-- Name: ix_tariff_rates_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tariff_rates_organization_id ON public.tariff_rates USING btree (organization_id);


--
-- Name: ix_tariff_rates_version_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tariff_rates_version_id ON public.tariff_rates USING btree (version_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_organization_id ON public.users USING btree (organization_id);


--
-- Name: declarations update_declarations_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_declarations_updated_at BEFORE UPDATE ON public.declarations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: organizations update_organizations_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON public.organizations FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: corrections corrections_declaration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.corrections
    ADD CONSTRAINT corrections_declaration_id_fkey FOREIGN KEY (declaration_id) REFERENCES public.declarations(id) ON DELETE CASCADE;


--
-- Name: corrections corrections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.corrections
    ADD CONSTRAINT corrections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: declarations declarations_approved_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.declarations
    ADD CONSTRAINT declarations_approved_by_user_id_fkey FOREIGN KEY (approved_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: declarations declarations_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.declarations
    ADD CONSTRAINT declarations_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: declarations declarations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.declarations
    ADD CONSTRAINT declarations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: good_list_entries good_list_entries_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.good_list_entries
    ADD CONSTRAINT good_list_entries_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: good_list_entries good_list_entries_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.good_list_entries
    ADD CONSTRAINT good_list_entries_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.knowledge_base_versions(id) ON DELETE CASCADE;


--
-- Name: knowledge_base_versions knowledge_base_versions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_base_versions
    ADD CONSTRAINT knowledge_base_versions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: knowledge_base_versions knowledge_base_versions_uploaded_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_base_versions
    ADD CONSTRAINT knowledge_base_versions_uploaded_by_user_id_fkey FOREIGN KEY (uploaded_by_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: tariff_rates tariff_rates_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tariff_rates
    ADD CONSTRAINT tariff_rates_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: tariff_rates tariff_rates_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tariff_rates
    ADD CONSTRAINT tariff_rates_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.knowledge_base_versions(id) ON DELETE CASCADE;


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict zWFIalHuiVXtzPoq2jTmbftnzVPEDl9pWiHOjy4OyBrPkbiUV7a8eRLA2J1yuI4

