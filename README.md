# Huawei Autoconfig

## What is this project?

This project was created to compose configuration files for Huawei switches fast and error-free. 
It can make it from scratch or use an existing configuration from D-Link or Huawei switch to transfer some thing like VLANS, port descriptions, etc. 
It has GUI which is Tk-based. The project was initially developed for Windows, so to use it in Linux a couple of additional steps will be required (described below)

## How does it look like?

!["huawei_autoconfig - Initial parameters"](https://github.com/pavel-piatetskii/huawei_autoconfig/blob/master/docs/initial_parameters.png)

The first window is called "Initial parameters". If we want to compose a config file from scratch, we will need to set up network parameters as well as main VLANs names and IDs. Also, a switch model should be chosen from the list of available models.

If we would like to replace an existing switch, this can be done by clicking on the "Replacement" button and choosing a configuration file of an existing switch. The parser I wrote assumes that the config file was fetched by the RANCID differ. Then, we will need to choose the model with which the existing switch should be replaced.


