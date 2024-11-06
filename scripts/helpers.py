def split_outside_quotes( seperator, line ):
    fields = line.split( seperator )
    openquotehavers = filter(
        lambda x: fields[x].count( '"' ) % 2 > 0,
        range( len( fields ) )
    )
    for a,b in reversed( [ x for x in zip(
            openquotehavers, openquotehavers
    )]):
        fields = fields[:a ]\
            + [ seperator.join(
                [ f.replace('"','') for f in fields[ a : b + 1 ] ]
            ) ]\
            + fields[ b + 1 : ]
    return [ field.strip(' "\n') for field in fields ]

def rows_from_csv_etc( fname, encoding = "utf-8" ):
    """assume the seperator is the most common char in a file out of
    comma, semocolon and tab. return an array with an entry for each
    line (excepting lines without the seperator), each split along the
    seperator, using split_outside_quotes() above to ignore seperators
    inside quotes.
    Throws any and all exeptions from IO right back to the caller."""
    with open( fname, "r", encoding = encoding ) as f:
        lines = f.readlines()
        
    sep_counts = { ",": 0,
                  ";": 0,
                  "\t": 0 }
    for line in lines:
        for cand_sep in sep_counts.keys():
            sep_counts[ cand_sep ] += line.count( cand_sep )
            
    seperator = ","
    for cand_sep in sep_counts.keys():
        if sep_counts[ cand_sep ] > sep_counts[ seperator ]:
            seperator = cand_sep 
        
    return [ split_outside_quotes( seperator, line )
             for line in lines if seperator in line
            ]

