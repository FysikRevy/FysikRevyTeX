import gspread, functools
from itertools import zip_longest
from config import configuration as conf
version = conf["Frontpage"]["version"]\
    .split(",")[-1]\
    .strip()

@functools.cache
def init_sheet():
    global gc
    gc = gspread.oauth()
    global sh
    sh = gc.open(conf["gspread"]["spreadsheet"])
    global sheet
    sheet = sh.worksheet(conf["gspread"]["worksheet"])
    global values
    values = sheet.get( "A2:Z" )
    global requests
    requests = []

    if not sheet.get( "A1" ):
        sheet.update("A1:G1",
                     [['Filnavn',
                       'Akt',
                       'Nummer',
                       'Fra version',
                       'Rekvisit',
                       'Ansvarlig',
                       'Beskrivelse'
                       ]]
                     )
        sheet.format("A1:1", { "textFormat": {"bold": True } } )

    return None
    

def send_props_to_gspread( revue ):
    init_sheet()
    global requests
    requests = []
    v = add_update_markers( fill_in_titles( values.copy() ) )
    crow = 0
    for act in revue.acts:
        act_start = crow
        for mat in act.materials:
            mat_start = crow
            for prop in mat.props:
                v = find_prop_move_here( v, prop, mat, crow )
                crow += 1
            crow, v = move_rest_mat_here( v, mat, crow )
            crow, v = write_mat_heads( v, mat, mat_start, crow )
        crow, v = finish_act( v, act, act_start, crow )
    v = cleanup_spares( v, crow )
    execute_batch_requests( v, requests )

def columnize_prop( prop, old_row=[] ):
    prop_row = ['','','',version,
                prop.prop,
                prop.responsible or '',
                prop.description or ''
                ]
    return [ prop or old for prop,old
             in zip_longest( prop_row, old_row, fillvalue='' ) ]

def fill_in_titles( value_table ):
    v = value_table
    for row,last_row in zip( v[1:],v ):
        for i in range( 3 ):
            try:
                row[i] = row[i] or last_row[i]
            except IndexError:
                pass
    return v

def add_update_markers( v ):
    return [ [ False ] + row for row in v ]

def find_prop_move_here( v, prop, mat, crow ):
    try:
        at = next( n for n,r in enumerate( v[crow:], start=crow )
                   if r[1] == mat.file_name
                   and len(r) > 5
                   and r[5] == prop.prop
                  )
        v = move_row( v, at, crow )
        v[crow] = update_row( v[crow],
                              [ None ] * 3 + [ version,
                                               None,
                                               prop.responsible or '',
                                               prop.description or ''
                                              ]
                             )
    except StopIteration:
        v = insert_row( v, crow, [True] + columnize_prop( prop ) )
    return v

def move_row( v, move_from, move_to ):
    if move_from == move_to:
        return v
    global requests
    requests += [{ "moveDimension": {
        "source": {
            "sheetId": sheet.id,
            "dimension": "ROWS",
            "startIndex": move_from + 1,
            "endIndex": move_from + 2
            },
        "destinationIndex": move_to + 1
        }}]
    v[ move_to : move_to ] = v[ move_from : move_from + 1 ]
    if move_from > move_to:
        move_from += 1
    v[ move_from : move_from + 1 ] = []
    return v

def insert_row( v, at, row ):
    global requests
    requests += [{ "insertDimension": {
        "range": {
            "sheetId": sheet.id,
            "dimension": "ROWS",
            "startIndex": at + 1,
            "endIndex": at + 2
            },
        "inheritFromBefore": False
        }}]
    v[ at : at ] = [ [ True ] + row[1:] ]
    return v

def move_rest_mat_here( v, mat, crow ):
    w = v.copy()
    c = crow
    deleted = 0
    for n,r in enumerate( v[crow:], start=crow ):
        try:
            if r[1] == mat.file_name:
                if any( r[8:] ):
                    w = move_row( w, n, c )
                    c += 1
                else:
                    w = delete_row( w, n - deleted )
                    deleted += 1
        except IndexError as e:
            w = delete_row( w, n - deleted )
            deleted += 1
    return c, w

def delete_row( v, row ):
    global requests
    requests += [{ "deleteDimension": {
        "range": {
            "sheetId": sheet.id,
            "dimension": "ROWS",
            "startIndex": row + 1,
            "endIndex": row + 2
            }}}]
    v[ row : row + 1 ] = []
    return v

def update_row( old_row, new_row ):
    return [ True ] \
        + ( new_row if not old_row[0]
            else [ old if new is None else new for new,old
                     in zip_longest( new_row, old_row[1:] )
                  ]
            )

def update_block_with_header( v, start, end, header_row, body_row ):
    return v[ :start ] \
        + [ update_row( v[start], header_row ) ] \
        + [ update_row( row, body_row )
            for row in v[ start + 1 : end ]
           ] \
        + v[ end: ]

def write_mat_heads( v, mat, start, end ):
    # empty row for material without props
    if start == end:
        v = insert_row(
            v, start, [True, mat.file_name, None, mat.title, version]
        )
        return start + 1, v
    return end, update_block_with_header(
        v, start, end,
        [ mat.file_name, None, mat.title ],
        ['', None, '']
    )

def finish_act( v, act, start, end ):
    try:
        fn = next( row[1] for n,row in enumerate( v[end:], start=end )
                    if row[2] == act.name and any( row[8:] ) )
        end, v = move_rest_mat_here(
            v,
            type('',(object,),{ "file_name": fn })(),
            end
        )
        return finish_act( v, act, start, end )
    except StopIteration:
        return end, update_block_with_header( v, start, end,
                                              [ None, act.name ],
                                              [ None, '' ]
                                             )

def cleanup_spares( v, end ):
    while end < len( v ):
        if any( v[end][8:] ):
            end += 1
        else:
            v = delete_row( v, end )
    return v

def execute_batch_requests( v, requests ):
    sh.batch_update( { "requests": requests,
                       "includeSpreadsheetInResponse": False
                       } )
    sheet.batch_update(
        [ {"range": "{0}:{0}".format( i + 2 ),
           "values": [ row[1:] ] }
          for i,row in enumerate( v ) if row[0] ]
        )
        
