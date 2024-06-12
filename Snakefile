# Snakefile

configfile: "config.yaml"

import yaml, os

with open("config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)



#rule all:
#    input:
#        expand("{data_path}snake.txt", zip, source_path=config["source_path"], data_path=config["data_path"])


rule initialize:
    input:
        "initialize.py"
    output:
        output_init = config["data_path"]
    params:
        source_path=config["source_path"],
        data_path=config["data_path"],
        separate=config["separate"],
        bulk_download=config["bulk_download"]
    shell:
        """
        module load geoconda
        python {input} "{params.source_path}" "{params.data_path}" "{params.separate}" "{params.bulk_download}"
        touch {output}
        """
        

rule download_images:
    input:
        "download_images.py",
        "initialized.txt"
    output:
        temp("images_downloaded.txt")
    params:
        source_path=config["source_path"],
        data_path=config["data_path"],
        bulk_download=config["bulk_download"]
    shell:
        """
        python {input} "{params.source_path}" "{params.data_path}" "{params.bulk_download}"
        touch {output}
        """

rule download_dem:
    input:
        "download_dem.py",
        "initialized.txt"
    output:
        temp("dem_downloaded.txt")
    params:
        source_path=config["source_path"],
        data_path=config["data_path"],
        bulk_download=config["bulk_download"]
    shell:
        """
        python {input} "{params.source_path}" "{params.data_path}" "{params.bulk_download}"
        touch {output}
        """

rule download_orbits:
    input:
        "download_orbits.py",
        "initialized.txt"
    output:
        temp("orbits_downloaded.txt")
    params:
        data_path=config["data_path"],
        bulk_download=config["bulk_download"]
    shell:
        """
        python {input} "{params.data_path}" "{params.bulk_download}"
        touch {output}
        """

rule download_weather:
    input:
        "download_weather.py",
        "initialized.txt"
    output:
        temp("weather_downloaded.txt")
    params:
        source_path=config["source_path"],
        data_path=config["data_path"]
    shell:
        """
        python {input} "{params.source_path}" "{params.data_path}"
        touch {output}
        """

rule process_images:
    input:
        "process_images.py",
        "initialized.txt",
        "images_downloaded.txt",
        "dem_downloaded.txt",
        "orbits_downloaded.txt"
        
    output:
        temp("images_processed.txt")
    params:
        source_path=config["source_path"],
        data_path=config["data_path"],
        bulk_download=config["bulk_download"]
    shell:
        """
        module load snap
        source snap_add_userdir {params.data_path}
        python3 {input} "{params.source_path}" "{params.data_path}" "{params.bulk_download}"
        touch {output}
        """

rule create_timeseries:
    input:
        "timeseries.py",
        "images_processed.txt"
    output:
        "{data_path}/{id}/timeseries_output.txt"
    params:
        source_path=config["source_path"],
        data_path=config["data_path"],
        bulk_download=config["bulk_download"],
        id="{id}"
    shell:
        """
        module load geoconda
        python {input} "{params.source_path}" "{params.data_path}" "{params.bulk_download}" "{params.id}"
        """