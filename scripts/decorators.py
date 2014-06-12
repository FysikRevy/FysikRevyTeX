from IPython import embed
import metadata as md

class valid_io:
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        # Check if input/output is in kwargs
        
        # Else check if there are strings in args that ends with .tex/.pdf

        # Check that there are no slashes in the file names
        # If there is, replace it with a dash

        pass



class checkcache:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, objtype):

        def wrapper(*args, **kwargs):
            metadata = md.MetaData()

            input_is_material = False
            input_is_tex_obj = False
            input_is_pdf_file = False
            input_is_list = False
            actor_in_list = False

            output_dir_defined = False
            
            if 'outputdir' in kwargs.keys():
                if kwargs['outputdir'] != '':
                    output_dir_defined = True



            fobj = None
            for arg in args:
                if type(arg).__name__ == 'Material':
                    fobj = arg
                    input_is_material = True
                    break
                
                elif type(arg).__name__ == 'TeX':
                    fobj = arg
                    input_is_tex_obj = True
                    break

                elif type(arg) is str and arg[-3:] == 'pdf':
                    fobj = arg
                    input_is_pdf_file = True
                    break

                elif type(arg) is list:
                    input_is_list = True
                    fobj = arg

                    if type(arg[0]).__name__ == 'TeX' and type(arg[1]) is str:
                        fobj = arg
                        input_is_tex_obj = True
                        break

                    for el in arg:
                        if type(el).__name__ == 'Actor':
                            # TODO
                            # check whether any file as been changed.
                            # Should we also check for an updated act overview,
                            # role list etc.? Might be relevant, but will definitely
                            # require a lot more merging...
                            actor_in_list = True

                        

            
            if input_is_material:
                if metadata.has_changed(fobj):
                    # The input was a file name, so the function is executed
                    # and modfication time is updated.
                    self.f(obj, *args, **kwargs)
                    fobj.has_been_texed = True

            elif input_is_tex_obj and output_dir_defined:
                if 'cache' in kwargs['outputdir'] and kwargs['pdfname'] != "":
                    # FIXME: problems if the whole revue is placed within a 'cache' directory.
                    if not os.path.isfile(os.path.join(path["pdf"], "cache", kwargs['pdfname'])):
                        self.f(obj, *args, **kwargs)

            elif input_is_list and actor_in_list:
                should_be_merged = False
                for el in fobj:
                    if type(el) is list:
                        for ell in el:
                            if type(ell).__name__ == 'Actor':
                                for role in ell.roles:
                                    for material in role.material:
                                        if metadata.has_changed(material):
                                            should_be_merged = True
                    if type(el).__name__ == 'Actor':
                        for role in el.roles:
                            for material in role.material:
                                if metadata.has_changed(material):
                                    should_be_merged = True
                    #elif metadata.has_changed(material):
                        # FIXME: PDFs will always have changed, since we don't have
                        # a good way of checking when e.g. the aktoversigt should be
                        # recreated.
                        #should_be_merged = True

                if should_be_merged:
                    self.f(obj, *args, **kwargs)
            #elif input_is_list and not actor_in_list:
            #        self.f(obj, *args, **kwargs)




            else:
                # The input was not a file name, so the function is executed:
                self.f(obj, *args, **kwargs)

        return wrapper


