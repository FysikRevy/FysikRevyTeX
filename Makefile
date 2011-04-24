skelfiles := .config.* */*.tex

%:
	@mkdir -p $(dir $@)
	@cp -r skel $@
	@cd $@; ln -s $(dir $@)RevyTeX/scripts/makefile_adm Makefile
	@cd $@; ln -s $(dir $@)RevyTeX/scripts/revy.sty revy.sty
	@cd $@; ln -s ../$(dir $@)RevyTeX/scripts/makefile_materials sange/Makefile
	@cd $@; ln -s ../$(dir $@)RevyTeX/scripts/makefile_materials sketches/Makefile
	@cd $@; ln -s ../$(dir $@)RevyTeX/scripts/makefile_materials video/Makefile
	@cd $@; ln -s ../$(dir $@)RevyTeX/scripts/revy.sty sange/revy.sty
	@cd $@; ln -s ../$(dir $@)RevyTeX/scripts/revy.sty sketches/revy.sty
	@cd $@; ln -s ../$(dir $@)RevyTeX/scripts/revy.sty video/revy.sty
	@scripts/config.sh $@
