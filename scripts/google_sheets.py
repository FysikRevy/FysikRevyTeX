import gspread, functools
from itertools import zip_longest
version = "test"
#from config import configuration as conf
# version = conf["Frontpage"]["version"]\
#     .split(",")[-1]\
#     .strip()

held_values = None

gc = gspread.oauth()
sh = gc.open("AutoRekvisitter2023")
sheet = sh.worksheet("Ark1")

#print(sheet.get_all_values())

    # if len( sheet.get_all_values() ) == 0:
    #     # initialiser tomt ark
    #     sheet.update("A1:G1",
    #                  [['Filnavn',
    #                    'Akt',
    #                    'Nummer',
    #                    'Fra version',
    #                    'Rekvisit',
    #                    'Ansvarlig',
    #                    'Beskrivelse'
    #                    ]]
    #                  )

    # held_values = sheet.get_all_values()[1:]

values = sheet.get( "A2:Z" )
updates = requests = []

@functools.cache
def list_sparse_column( coln ):
    return [ (n,r[coln]) for n,r
             in enumerate( values ) if not r[coln] == "" ]

@functools.cache
def sparse_column_range( coln, content ):
    found_index = next(( n for n,r in enumerate( list_sparse_column( coln ) )
                         if r[1] == content ),
                       len( list_sparse_column( coln ) )
                       )
    # lookup = list_acts() + [ -1, '' ]
    # return lookup[ act_index ][0], lookup[ act_index + 1 ][0]
    return tuple( el[0] for el
                  in ( list_sparse_column( coln ) + [( None,),(0,)] )\
                    [ found_index: ][:2]
                 )

def act_range( act ):
    return sparse_column_range( 1, act )

def fname_range( fname ):
    return sparse_column_range( 0, fname )

def compare_sheet( revue ):
    v = values
    for act in revue.acts:
        if v[0][0] != act.name:
            break
        return "a"
    return "b"

def find_file( fn ):
    return next((n for n,x in enumerate( values )
                 if x[0] == fn
                 ), None )

def act_from_sheet( act ):
    act_list = list_acts() + [(-1,'')]
    acti = next((n for n,a in enumerate( act_list )
                 if a[1] == act), -1)
    return values[act_list[acti][0]:act_list[acti + 1][0]]

def insert_act( insert_at, act ):
    # act_from_sheet = values[
    #     next(x[0] for x in list_acts() if x[1] == act.name)
    act_rows = []
    for m in act.materials:
        mi = find_file( m.file_name )
        if not mi is None:
            act_rows += values[ mi ]
            values[ mi ] = []
        else:
            act_rows += []

def columnize_prop( prop, old_row=[] ):
    prop_row = ['','','',version,
                prop.prop,
                prop.responsible,
                prop.description
                ]
    return [ prop or old for prop,old
             in zip_longest( prop_row, old_row, fillvalue='' ) ]

def columnize_material( m ):
    mat_rows = [ columnize_prop( prop )
                 for prop in m.props ]
    try:
        mat_rows[0][0] = m.file_name 
        mat_rows[0][2] = m.title 
        return mat_rows
    except IndexError:
        print( "No props for '{}' are declared.".format(m.title))
        return []

def rows_from_tex( revue ):
    splat = []
    for act in revue.acts:
        act_rows = [ row for m in act.materials
                         for row in columnize_material( m ) ]
        try:
            act_rows[0][1] = act.name
        except IndexError:
            pass
        splat += act_rows
    return splat

def dump_everything( revue ):
    sheet.update( 'A2:Z', rows_from_tex( revue ) )
    # print(rows_from_tex( revue ))

def with_compare( revue ):
    splat = []
    for act in revue.acts:
        act_splat = []
        for mat in act.materials:
            material_splat = []
            material_range = fname_range( mat.file_name )
            for prop in mat.props:
                prop_row_i = next(
                    ( n for n,r in [ x for x in 
                        enumerate( values )][ material_range[0]
                                             : material_range[1] ]
                      if r[4] == prop.prop
                     ), None
                )
                try:
                    material_splat += [
                        columnize_prop( prop, values[ prop_row_i ] )
                    ]
                    values[ prop_row_i ][3:7] = [''] * 4
                except TypeError as e:
                    if str(e) != "list indices must be integers or "\
                               + "slices, not NoneType":
                        raise e
                    material_splat += [ columnize_prop( prop ) ]
            for n,r in enumerate( values[ material_range[0]
                                          : material_range[0] ] ):
                if r[4] and any( r[7:] ):
                    material_splat += values[ n ]
                    values[ n ][3:7] = [''] * 4
            try:
                values[ material_range[0] ][0] = ''
                values[ material_range[0] ][2] = ''
            except TypeError as e:
                if str(e) != "list indices must be integers or "\
                           + "slices, not NoneType":
                    raise e
            try:
                material_splat[0][0] = mat.file_name
                material_splat[0][2] = mat.title
            except IndexError:
                material_splat = [
                    [mat.file_name,'',mat.title,version] + [''] * 3
                ]
            act_splat += material_splat
        rem_mat_is = [ n for n,r
                       in [ x for x in enumerate( values )]
                       [ act_range( act.name )[0]
                         : act_range( act.name )[1] ]
                       if r[0] != ''
                      ] + [ act_range( act.name)[1] ]
        for start,end in zip( rem_mat_is, rem_mat_is[1:] ):
            act_splat += values[ start:end ]
            values[ start ][0] = values[ start ][2] = ''
        try:
            values[ act_range( act.name )[0] ][1] = ''
        except TypeError as e:
            if str(e) != "list indices must be integers or "\
                       + "slices, not NoneType":
                raise e
        act_splat[0][1] = act.name
        splat += act_splat
    # print( splat )
    sheet.update( "A2:Z", splat )

def fill_in_titles( value_table ):
    v = value_table
    for row,last_row in zip( v[1:],v ):
        for i in range( 3 ):
            row[i] = row[i] or last_row[i]
    return v

def update_steps( revue ):
    updates = requests = []
    v = fill_in_titles( values )
    src, dst = 0,0
    for act in revue.acts:
        act_start = src
        for mat in act.materials:
            mat_start = src
            for prop in mat.props:
                v = find_prop_move_here( v, prop, dst )
                src += 1
                dst += 1
            move_rest_mat_here()
            write_mat_heads()
        write_act_name()
    cleanup_spares()

def find_prop_move_here( v, prop, dst):
    try:
        at = next( n for n,r in enumerate( v )
                   if n >= src
                   and r[0] == mat.file_name
                   and r[4] == prop.prop
                  )
        v = move_row( v, at, dst )
    except StopIteration:
        v = insert_row( v, dst, columnize_prop( prop ) )
    return v

def move_row( v, move_from, move_to ):
    requests += { "moveDimension": {
        "source": {
            "sheetId": sheet.id,
            "dimension": "ROWS",
            "startIndex": move_from + 1,
            "endIndex": move_from + 2
            },
        "destinationIndex": move_to + 1
        }}
    v[ move_to : move_to ] = v[ move_from : move_from + 1 ]
    v[ move_from : move_from + 1 ] = []
    return v

def insert_row( v, dst, row ):
    pass
