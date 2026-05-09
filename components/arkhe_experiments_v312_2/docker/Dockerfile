FROM condaforge/miniforge3:latest

# Set working directory
WORKDIR /app

# Copy environment file
COPY environment.yml .

# Create the conda environment
RUN conda env create -f environment.yml && \
    conda clean -a -y

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "arkhe-stat-env", "/bin/bash", "-c"]

# Set environment variables
ENV PATH /opt/conda/envs/arkhe-stat-env/bin:$PATH

# Copy the rest of the application
COPY ../ /app/

# Entrypoint
CMD ["/bin/bash"]
