#!/usr/bin/env python
# coding: utf-8
# gatk3_bam_processing_scatter_gather 0.0.1
# Generated by dx-app-wizard.
#
# Scatter-process-gather execution pattern: Your app will split its
# input into multiple pieces, each of which will be processed in
# parallel, after which they are gathered together in some final
# output.
#
# This pattern is very similar to the "parallelized" template.  What
# it does differently is that it formally breaks out the "scatter"
# phase as a separate black-box entry point in the app.  (As a side
# effect, this requires a "map" entry point to call "process" on each
# of the results from the "scatter" phase.)
#
# Note that you can also replace any entry point in this execution
# pattern with an API call to run a separate app or applet.
#
# The following is a Unicode art picture of the flow of execution.
# Each box is an entry point, and vertical lines indicate that the
# entry point connected at the top of the line calls the entry point
# connected at the bottom of the line.  The letters represent the
# different stages in which the input is transformed, e.g. the output
# of the "scatter" entry point ("array:B") is given to the "map" entry
# point as input.  The "map" entry point calls as many "process" entry
# points as there are elements in its array input and gathers the
# results in its array output.
#
#          ┌──────┐
#       A->│ main │->D (output from "postprocess")
#          └┬─┬─┬─┘
#           │ │ │
#          ┌┴──────┐
#       A->│scatter│->array:B
#          └───────┘
#             │ │
#            ┌┴──────────────┐
#   array:B->│      map      │->array:C
#            └─────────┬─┬─┬─┘
#               │      │ . .
#               │     ┌┴──────┐
#               │  B->│process│->C
#               │     └───────┘
#            ┌──┴────────┐
#   array:C->│postprocess│->D
#            └───────────┘
#
# A = original app input, split up by "scatter" into pieces of type B
# B = an input that will be provided to a "process" entry point
# C = the output of a "process" entry point
# D = app output aggregated from the outputs of the "process" entry points
#
# See https://wiki.dnanexus.com/Developer-Portal for documentation and
# tutorials on how to modify this file.
#
# DNAnexus Python Bindings (dxpy) documentation:
#   http://autodoc.dnanexus.com/bindings/python/current/

import os
import dxpy
import logging
import time


logger = logging.getLogger(__name__)
logger.addHandler(dxpy.DXLogHandler())
logger.propagate = False


try:
    from dx_applet_utilities import (
        common_job_operations as dx_utils,
        manage_command_execution as dx_exec,
        prepare_job_resources as dx_resources,
        prepare_scatter_gather_jobs as dx_scatter)
except ImportError:
    logger.error("Make sure to add the dx_applet_utilities to execDepends in dxapp.json!")
    sys.exit(1)


@dxpy.entry_point("gatk_realignment")
def gatk_realignment(bam_files, reference, sampleId, downsample,
    downsample_fraction=None, regions_file=None, padding=None, indel_vcf=None,
    advanced_rtc_options=None, advanced_ir_options=None, loglevel=None):

    """Starts with scattered BAM files to run GATK Realignment.

    :param: `bam_files`:
    :param: `reference`:
    :param: `sampleId`:
    :param: `downsample`:
    :param: `downsample_fraction`:
    :param: `regions_file`:
    :param: `padding`
    :param: `indel_vcf`:
    :param: `advanced_rtc_options`:
    :param: `advanced_ir_options`:
    :param: `loglevel`:
    :returns: An array of file objects for the GATK Realignment command output
    """


@dxpy.entry_point("gatk_base_recalibrator")
def gatk_base_recalibrator(bam_files, reference, regions_file=None, padding=None,
    indel_vcf=None, dbsnp=None, advanced_br_options=None, loglevel=None):

    """Takes the output from scattered GATK Realignment jobs (gatk_realignment)
    to run GATK BaseRecalibrator job (gatk_base_recalibrator)

    :param: `bam_files`:
    :param: `reference`:
    :param: `regions_file`:
    :param: `padding`
    :param: `indel_vcf`:
    :param: `dbsnp`:
    :param: `advanced_br_options`:
    :param: `loglevel`:
    :returns: A file object for the GATK BaseRecalibrator command output
    """

    # Set up string variables that are not required

    if not advanced_pr_options:
        advanced_pr_options = ""

    # Set up execution environment

    logger.setLevel(loglevel)
    cpus = dx_resources.number_of_cpus(1.0)
    max_ram = dx_resources.max_memory(0.85)
    logger.info("# of CPUs:{0}\nMax RAM:{1}".format(cpus, max_ram))

    temp_directories = [
        "in/",
        "genome/",
        "tmp/preprocessing/",
        "out/output_bqsr/"
    ]

    for temp_directory in temp_directories:
        create_dir = dx_exec.execute_command("mkdir -p {0}".format(
            temp_directory))
        dx_exec.check_execution_syscode(create_dir, "Created: {0}".format(
            temp_directory))
        chmod_dir = dx_exec.execute_command("chmod 777 -R {0}".format(
            temp_directory))
        dx_exec.check_execution_syscode(chmod_dir, "Modified: {0}".format(
            temp_directory))

    # The following line(s) initialize your data object inputs on the platform
    # into dxpy.DXDataObject instances that you can start using immediately.

    reference_filename = "in/reference/{0}".format(
        dxpy.DXFile(reference).describe()["name"])

    bam_filenames = []
    for index, bam_file in enumerate(bam_files):

        # DNAnexus has this funky behavior when you have > 9 files, it creates
        # a folder in/parameter/08/file - this resolves that issue
        if len(bam_files) > 9 and index < 10:
            index = "0{0}".format(index)

        bam_filenames.append("in/bam_files/{0}/{1}".format(index,
            dxpy.DXFile(bam_file).describe()["name"]))

    indel_vcf_files = []
    knownsites_parameter = ""
    if indel_vcf:
        for index, file_object in enumerate(indel_vcf):
            filename = "in/indel_vcf/{0}/{1}".format(index,
                dxpy.DXFile(file_object).describe()["name"])
            indel_vcf_files.append(filename)
            knownsites_parameter += "-knownSites {0} ".format(filename)

    if dbsnp:
        dbsnp = "in/dbsnp/{0}".format(dxpy.DXFile(dbsnp).describe()["name"])
        knownsites_parameter += "-knownSites {0} ".format(dbsnp)

    regions_parameter = ""
    if regions_file:
        regions_file = "in/regions_file/{0}".format(
            dxpy.DXFile(regions_file).describe()["name"])
        regions_parameter = "-L {0} ".format(regions_file)

        if padding:
            regions_parameter += "-ip {0} ".format(padding)

    # The following line(s) download your file inputs to the local file system
    # using variable names for the filenames.

    dx_download_inputs_cmd = "dx-download-all-inputs --parallel"
    download_inputs = dx_exec.execute_command(dx_download_inputs_cmd)
    dx_exec.check_execution_syscode(download_inputs, "Download input files")

    # The following line(s) are the body of the applet that
    # executes the bioinformatics processes

    # Prepare refernce genome for GATK

    unzip_reference_genome_cmd = "gzip -dc {0} > genome/genome.fa".format(
        reference_filename)
    unzip_reference_genome = dx_exec.execute_command(unzip_reference_genome_cmd)
    dx_exec.check_execution_syscode(unzip_reference_genome, "Unzip reference genome")
    reference_filename = "genome/genome.fa"

    reference_faidx_cmd = "samtools faidx {0}".format(reference_filename)
    reference_faidx = dx_exec.execute_command(reference_faidx_cmd)
    dx_exec.check_execution_syscode(reference_faidx, "Reference samtools faidx")

    reference_dict = "genome/genome.dict"
    reference_dict_cmd = "samtools dict {0} > {1}".format(reference_filename, reference_dict)
    reference_dict = dx_exec.execute_command(reference_dict_cmd)
    dx_exec.check_execution_syscode(reference_dict, "Reference samtools dict")

    # Index VCFs for GATK using tabix

    if dbsnp:
        dbsnp_tabix_cmd = "tabix -p vcf {0}".format(dbsnp)
        dbsnp_tabix = dx_exec.execute_command(dbsnp_tabix_cmd)
        dx_exec.check_execution_syscode(dbsnp_tabix, "Tabix of dbSNP VCF")

    if indel_vcf:
        for vcf_file in indel_vcf_files:
            indel_vcf_tabix_cmd = "tabix -p vcf {0}".format(vcf_file)
            indel_vcf_tabix = dx_exec.execute_command(indel_vcf_tabix_cmd)
            dx_exec.check_execution_syscode(indel_vcf_tabix, "Tabix of {0}".format(vcf_file))

    # Merge BAM files if there are more than one
    if len(bam_filenames) > 1:
        merged_bam = "tmp/preprocessing/merged.bam"
        merge_bam_cmd = "sambamba merge -t {0} {1} {2}".format(
            cpus, merged_bam, " ".join(bam_filenames))
        merge_bam = dx_exec.execute_command(merge_bam_cmd)
        dx_exec.check_execution_syscode(merge_bam, "Merge BAM")

        sorted_bam = "tmp/preprocessing/sorted.bam"
        sort_bam_cmd = "sambamba sort -t {0} {1} -o {2}".format(
            cpus, merged_bam, sorted_bam)
        sort_bam = dx_exec.execute_command(sort_bam_cmd)
        dx_exec.check_execution_syscode(sort_bam, "Sort merged BAM")

    br_input = sorted_bam
    br_output = "out/output_bqsr/recalibration.grp"

    br_cmd = "java -Xmx{0}m -jar /opt/jar/GenomeAnalysisTK.jar ".format(max_ram)
    br_cmd += "-T BaseRecalibrator {0} -nct {1} ".format(advanced_br_options, cpus)
    br_cmd += "-R {0} {1} {2} -I {3} -o {4}".format(reference_filename,
        knownsites_parameter, regions_parameter, br_input, br_output)

    gatk_br = dx_exec.execute_command(br_cmd)
    dx_exec.check_execution_syscode(gatk_br, "GATK BaseRecalibrator")

    # The following line(s) use the Python bindings to upload your file outputs
    # after you have created them on the local file system.  It assumes that you
    # have used the output field name for the filename for each output, but you
    # can change that behavior to suit your needs.

    dx_upload_outputs_cmd = "dx-upload-all-outputs --parallel"
    download_outputs = dx_exec.execute_command(dx_upload_outputs_cmd)
    dx_exec.check_execution_syscode(download_outputs, "Upload outputs")

    # The following line fills in some basic dummy output and assumes
    # that you have created variables to represent your output with
    # the same name as your output fields.

    upload_output_object = dx_utils.load_json_from_file("job_output.json")
    return dx_utils.prepare_job_output(
        dx_output_object=upload_output_object,
        must_be_array=False
    )



@dxpy.entry_point("gatk_apply_bqsr")
def gatk_apply_bqsr(bam_files, gatk_br_output, reference, sampleId,
    regions_file=None, padding=None, advanced_pr_options=None, loglevel=None):

    """Takes the output from scattered GATK Realignment jobs (gatk_realignment)
    and the output of GATK BaseRecalibrator job (gatk_base_recalibrator) to run
    GATK PrintReads -BQSR

    :param: `bam_files`:
    :param: `gatk_br_output`:
    :param: `reference`:
    :param: `sampleId`:
    :param: `regions_file`:
    :param: `padding`
    :param: `advanced_pr_options`:
    :param: `loglevel`:
    :returns: Array of dx file objects that are recalibrated BAM and CRAM files
    """

    # Set up string variables that are not required

    if not advanced_pr_options:
        advanced_pr_options = ""

    # Set up execution environment

    logger.setLevel(loglevel)
    cpus = dx_resources.number_of_cpus(1.0)
    max_ram = dx_resources.max_memory(0.85)
    logger.info("# of CPUs:{0}\nMax RAM:{1}".format(cpus, max_ram))

    temp_directories = [
        "in/",
        "genome/",
        "out/output_recalibrated_bam/",
        "out/output_recalibrated_cram/",
        "tmp/recalibration/"
    ]

    for temp_directory in temp_directories:
        create_dir = dx_exec.execute_command("mkdir -p {0}".format(
            temp_directory))
        dx_exec.check_execution_syscode(create_dir, "Created: {0}".format(
            temp_directory))
        chmod_dir = dx_exec.execute_command("chmod 777 -R {0}".format(
            temp_directory))
        dx_exec.check_execution_syscode(chmod_dir, "Modified: {0}".format(
            temp_directory))

    # The following line(s) initialize your data object inputs on the platform
    # into dxpy.DXDataObject instances that you can start using immediately.

    reference_filename = "in/reference/{0}".format(
        dxpy.DXFile(reference).describe()["name"])

    bam_filenames = []
    for index, bam_file in enumerate(bam_files):

        # DNAnexus has this funky behavior when you have > 9 files, it creates
        # a folder in/parameter/08/file - this resolves that issue
        if len(bam_files) > 9 and index < 10:
            index = "0{0}".format(index)

        bam_filenames.append("in/bam_files/{0}/{1}".format(index,
            dxpy.DXFile(bam_file).describe()["name"]))

    regions_parameter = ""
    if regions_file:
        regions_file = "in/regions_file/{0}".format(
            dxpy.DXFile(regions_file).describe()["name"])
        regions_parameter = "-L {0} ".format(regions_file)

        if padding:
            regions_parameter += "-ip {0} ".format(padding)

    # The following line(s) download your file inputs to the local file system
    # using variable names for the filenames.

    dx_download_inputs_cmd = "dx-download-all-inputs --parallel"
    download_inputs = dx_exec.execute_command(dx_download_inputs_cmd)
    dx_exec.check_execution_syscode(download_inputs, "Download input files")

    # The following line(s) are the body of the applet that
    # executes the bioinformatics processes

    # Prepare refernce genome for GATK

    unzip_reference_genome_cmd = "gzip -dc {0} > genome/genome.fa".format(
        reference_filename)
    unzip_reference_genome = dx_exec.execute_command(unzip_reference_genome_cmd)
    dx_exec.check_execution_syscode(unzip_reference_genome, "Unzip reference genome")
    reference_filename = "genome/genome.fa"

    reference_faidx_cmd = "samtools faidx {0}".format(reference_filename)
    reference_faidx = dx_exec.execute_command(reference_faidx_cmd)
    dx_exec.check_execution_syscode(reference_faidx, "Reference samtools faidx")

    reference_dict = "genome/genome.dict"
    reference_dict_cmd = "samtools dict {0} > {1}".format(reference_filename, reference_dict)
    reference_dict = dx_exec.execute_command(reference_dict_cmd)
    dx_exec.check_execution_syscode(reference_dict, "Reference samtools dict")

    # GATK PrintReads -BQSR

    for bam_file in bam_filenames:
        pr_input = bam_file
        pr_output = "out/output_recalibrated_bam/{0}.recalibrated.bam".format(sampleId)

        pr_cmd = "java -Xmx{0}m -jar /opt/jar/GenomeAnalysisTK.jar ".format(max_ram)
        pr_cmd += "-T PrintReads {0} -R {1} ".format(advanced_pr_options, reference_filename)
        pr_cmd += "-BQSR {0} -I {1} -o {2}".format(br_output, pr_input, pr_output)

        idx_bam_cmd = "sambamba index -p -t {0} {1}".format(cpus, bam_file)
        idx_bam = dx_exec.execute_command(idx_bam_cmd)
        dx_exec.check_execution_syscode(idx_bam, "Index BAM file")

        gatk_pr = dx_exec.execute_command(pr_cmd)
        dx_exec.check_execution_syscode(gatk_pr, "GATK Apply BQSR")

        # Convert recalibrated BAM to CRAM for archiving (Variant callers will
        # support variant calling from CRAM soon!)

        cram_file = "out/output_recalibrated_cram/{0}.recalibrated.cram".format(
            sampleId)
        cram_cmd = "sambamba view -f cram -t {0} -T {1} {2} -o {3}".format(
            cpus, reference_filename, pr_output, cram_file)

        cram = dx_exec.execute_command(cram_cmd)
        dx_exec.check_execution_syscode(cram, "Convert BAM to CRAM")

    # Remove index files - no need to store these for now :)

    rm_bai_files_cmd = "rm -rf out/output_recalibrated_bam/*bai"
    rm_cai_files_cmd = "rm -rf out/output_recalibrated_cram/*cai"

    rm_bai_files = dx_exec.execute_command(rm_bai_files_cmd)
    dx_exec.check_execution_syscode(rm_bai_files, "Remove *bai")

    rm_cai_files = dx_exec.execute_command(rm_cai_files_cmd)
    dx_exec.check_execution_syscode(rm_cai_files, "Remove *cai")

    # The following line(s) use the Python bindings to upload your file outputs
    # after you have created them on the local file system.  It assumes that you
    # have used the output field name for the filename for each output, but you
    # can change that behavior to suit your needs.

    dx_upload_outputs_cmd = "dx-upload-all-outputs --parallel"
    download_outputs = dx_exec.execute_command(dx_upload_outputs_cmd)
    dx_exec.check_execution_syscode(download_outputs, "Upload outputs")

    # The following line fills in some basic dummy output and assumes
    # that you have created variables to represent your output with
    # the same name as your output fields.

    upload_output_object = dx_utils.load_json_from_file("job_output.json")
    return dx_utils.prepare_job_output(
        dx_output_object=upload_output_object,
        must_be_array=False
    )


@dxpy.entry_point("gather")
def map_entry_point(**kwargs):

    """This takes care of gathering all input from scattered jobs."""

    output = {}
    for output_name, scatter_jobs in kwargs.items():
        ret = []
        for job in scatter_jobs:
            for file_object in job:
                ret.append(dxpy.dxlink(file_object["$dnanexus_link"]))

        output[output_name] = ret

    return output


@dxpy.entry_point("main")
def main(bam_files, sampleId, padding, reference, loglevel, number_of_nodes,
    downsample, downsample_fraction, regions_file=None, indel_vcf=None,
    dbsnp=None, advanced_rtc_options=None, advanced_ir_options=None,
    advanced_br_options=None, advanced_pr_options=None):

    """This is a dx applet that runs on the DNAnexus platform. This will run
    GATK3 best practices pipeline using scatter gather. This is very useful for
    processing WGS datasets. This function is the controller of the pipeline,
    which will scatter data, process it and then gather it for final processing.

    :param: `bam_files`:
    :param: `sampleId`:
    :param: `padding`:
    :param: `reference`:
    :param: `loglevel`:
    :param: `number_of_nodes`
    :param: `downsample`:
    :param: `downsample_fraction`:
    :param: `regions_file`:
    :param: `indel_vcf`:
    :param: `dbsnp`:
    :param: `advanced_rtc_options`:
    :param: `advanced_ir_options`:
    :param: `advanced_br_options`:
    :param: `advanced_pr_options`:
    """

    logger.setLevel(loglevel)
    logger.info("GATK3 scatter gather controller. Number of nodes for scatter jobs: {0}".format(number_of_nodes))

    # Balance jobs based on the file sizes of file from input

    file_sizes = {}
    file_objects = {}
    for bam_file in bam_files:
        file_size = int(dxpy.DXFile(bam_file).describe()["size"])
        file_name = dxpy.DXFile(bam_file).describe()["name"]
        file_sizes[file_name] = file_size
        file_objects[file_name] = bam_file

    balanced_jobs_object = dx_scatter.distribute_files_by_size(
        file_sizes=file_sizes,
        dx_file_objects=file_objects,
        number_of_nodes=number_of_nodes)

    # GATK in/del realignment phase

    gatk_rtc_ir_jobs = []
    for job_name, file_objects in balanced_jobs_object.items():

        logger.info("Create GATK3 Realignment Node")
        gatk_rtc_ir_jobs.append(
            dxpy.new_dxjob(
                fn_input={
                    "bam_files": file_objects,
                    "reference": reference,
                    "regions_file": regions_file,
                    "padding": padding,
                    "indel_vcf": indel_vcf,
                    "sampleId": sampleId,
                    "advanced_rtc_options": advanced_rtc_options,
                    "advanced_ir_options": advanced_ir_options,
                    "downsample": downsample,
                    "downsample_fraction": downsample_fraction,
                    "loglevel": loglevel
                },
                fn_name="gatk_realignment"
            )
        )

    # GATK3 BaseRecalibrator phase

    # This will gather the input from all the GATK3 Realignment nodes

    logger.info("Gather all GATK3 Realignment Output")

    kwargs = {
        "output_downsample_bams": [job.get_output_ref("output_downsample_bams")
            for job in gatk_rtc_ir_jobs],
        "output_realigned_bams": [job.get_output_ref("output_realigned_bams")
            for job in gatk_rtc_ir_jobs]
    }

    gather_gatk_rtc_ir_jobs = dxpy.new_dxjob(
        fn_input=kwargs,
        fn_name="gather",
    	depends_on=gatk_rtc_ir_jobs
    )

    # This will send all the realigned BAM files to the BaseRecalibrator node

    logger.info("Create GATK3 BaseRecalibrator Node")

    gatk_br_job = dxpy.new_dxjob(
        fn_input={
            "bam_files": gather_gatk_rtc_ir_jobs.get_output_ref("output_downsample_bams") if downsample else gather_gatk_rtc_ir_jobs.get_output_ref("output_realigned_bams"),
            "reference": reference,
            "regions_file": regions_file,
            "padding": padding,
            "indel_vcf": indel_vcf,
            "dbsnp": dbsnp,
            "advanced_br_options": advanced_br_options,
            "loglevel": loglevel
        },
        fn_name="gatk_base_recalibrator",
        depends_on=[gather_gatk_rtc_ir_jobs]
    )

    # GATK Apply BQSR

    gatk_apply_bqsr_jobs = []
    for gatk_rtc_ir_job in gatk_rtc_ir_jobs:

        logger.info("Create GATK3 Apply BQSR Node")
        gatk_apply_bqsr_jobs.append(
            dxpy.new_dxjob(
                fn_input={
                    "bam_files": gatk_rtc_ir_job.get_output_ref("output_realigned_bams"),
                    "BR_output": gatk_br_job.get_output_ref("output_bqsr"),
                    "reference": reference,
                    "regions_file": regions_file,
                    "padding": padding,
                    "dbsnp": dbsnp,
                    "sampleId": sampleId,
                    "advanced_pr_options": advanced_pr_options,
                    "loglevel": loglevel
                },
                fn_name="gatk_apply_bqsr",
                depends_on = gatk_rtc_ir_jobs + [gatk_br_job]
            )
        )

    # Gather all Apply BQSR output and finish the pipeline

    logger.info("Gather all GATK Apply BQSR calling job outputs")

    kwargs = {
        "output_recalibrated_bam": [job.get_output_ref("output_recalibrated_bam")
            for job in gatk_apply_bqsr_jobs],
        "output_recalibrated_cram": [job.get_output_ref("output_recalibrated_cram")
            for job in gatk_apply_bqsr_jobs]
    }

    gather_gatk_apply_bqsr_jobs = dxpy.new_dxjob(
        fn_input=kwargs,
        fn_name="gather",
    	depends_on=gatk_apply_bqsr_jobs
    )


    output = {}
    output["output_recalibrated_bam"] = gather_gatk_apply_bqsr_jobs.get_output_ref("output_recalibrated_bam")
    output["output_recalibrated_cram"] = gather_gatk_apply_bqsr_jobs.get_output_ref("output_recalibrated_cram")
    return output

dxpy.run()
