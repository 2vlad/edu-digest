-- Enable RLS for all tables
ALTER TABLE public.run_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.processed_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.channels ENABLE ROW LEVEL SECURITY;

-- Create policies for run_logs (allow authenticated users to read)
CREATE POLICY "Allow authenticated read access" ON public.run_logs
    FOR SELECT
    TO authenticated
    USING (true);

-- Create policies for settings (allow authenticated users to read/write)
CREATE POLICY "Allow authenticated read access" ON public.settings
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated write access" ON public.settings
    FOR ALL
    TO authenticated
    USING (true);

-- Create policies for processed_messages (allow authenticated users to read/write)
CREATE POLICY "Allow authenticated read access" ON public.processed_messages
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated write access" ON public.processed_messages
    FOR ALL
    TO authenticated
    USING (true);

-- Create policies for channels (allow authenticated users to read/write)
CREATE POLICY "Allow authenticated read access" ON public.channels
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated write access" ON public.channels
    FOR ALL
    TO authenticated
    USING (true);

-- If you want to allow service role full access (for backend operations)
CREATE POLICY "Service role full access" ON public.run_logs
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "Service role full access" ON public.settings
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "Service role full access" ON public.processed_messages
    FOR ALL
    TO service_role
    USING (true);

CREATE POLICY "Service role full access" ON public.channels
    FOR ALL
    TO service_role
    USING (true);