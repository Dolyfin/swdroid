# install.sh
export CMAKE_ARGS="-DGGML_BLAS=ON;-DGGML_BLAS_VENDOR=OpenBLAS"
pip install -r requirements.txt --break-system-packages
pip install --no-cache-dir --force-reinstall llama-cpp-python --break-system-packages