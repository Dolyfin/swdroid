# install.sh
export CMAKE_ARGS="-DGGML_BLAS=ON;-DGGML_BLAS_VENDOR=OpenBLAS"
pip install --no-cache-dir --force-reinstall llama-cpp-python
pip install -r requirements.txt