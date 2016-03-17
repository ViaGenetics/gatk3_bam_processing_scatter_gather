# gatk3_bam_processing_scatter_gather Developer Readme

<!--
TODO: Please edit this Readme.developer.md file to include information
for developers or advanced users, for example:

* Information about app internals and implementation details
* How to report bugs or contribute to development
-->

## Running this app with additional computational resources

This app has the following entry points:

* main
* gatk_realignment
* gatk_base_recalibrator
* gatk_apply_bqsr
* gather

When running this app, you can override the instance type to be used for each
entry point by providing the ``systemRequirements`` field to
```/applet-XXXX/run``` or ```/app-XXXX/run```, as follows:

    {
      systemRequirements: {
        "main": {"instanceType": "mem1_ssd1_x2"},
        "gatk_realignment": {"instanceType": "mem1_ssd1_x4"},
        "gatk_base_recalibrator": {"instanceType": "mem1_ssd2_x8"},
        "gatk_apply_bqsr": {"instanceType": "mem1_ssd1_x4"},
        "gather": {"instanceType": "mem1_ssd1_x2"}
      },
      [...]
    }

See <a
href="https://wiki.dnanexus.com/API-Specification-v1.0.0/IO-and-Run-Specifications#Run-Specification">Run
Specification</a> in the API documentation for more information about the
available instance types.
