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
    return fields

