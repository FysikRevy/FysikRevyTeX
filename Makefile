skelfiles := .config.* */*.tex

%:
	@mkdir -p $(dir $@)
	@cp -rL skel $@
	@scripts/config.sh $@
