NAME=jxserving
PACKAGE_DIR=build/package-$(arch)
EXTRACT_DIR=jxserving

version=$(shell git tag -l "v*" --points-at HEAD | tail -n 1 | tail -c +2 )
commit=$(shell git rev-parse --short HEAD)
builddate=$(shell date "+%m/%d/%Y %R %Z")
arch?=arm64

.PHONY: build debian clean check_version push_to_source

check_version:
ifeq ($(version),)
	$(error No version tag found)
endif
	
build: check_version
	python3 build_release.py

debian: check_version build
	mkdir -p $(PACKAGE_DIR)/$(EXTRACT_DIR)
	cp -r release-pack/* $(PACKAGE_DIR)/$(EXTRACT_DIR)
	echo $(version) > $(PACKAGE_DIR)/$(EXTRACT_DIR)/VERSION
	
	mkdir -p $(PACKAGE_DIR)/DEBIAN/
	sed -e "s/REPLACE_VERSION/$(version)/g" -e "s/REPLACE_ARCH/$(arch)/" DEBIAN/control > $(PACKAGE_DIR)/DEBIAN/control
	dpkg -b $(PACKAGE_DIR) build/$(NAME)_$(version)_$(arch).deb

	rm -rf $(PACKAGE_DIR)

push_to_source:
	bash scripts/upload.sh

clean:
	rm -rf build/
	rm -rf release-pack/