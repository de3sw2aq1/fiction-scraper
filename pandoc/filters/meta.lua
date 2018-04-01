function Meta(meta)
    local f = io.open(meta.metadata_file, 'r')
    local content = f:read('*a')
    f:close()
    return pandoc.read(content).meta
end
