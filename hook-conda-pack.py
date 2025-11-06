from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
datas = []
binaries = []

binaries += collect_dynamic_libs('llama_cpp')

datas  += collect_data_files('pandas', subdir='core')
datas  += collect_data_files('tqdm')