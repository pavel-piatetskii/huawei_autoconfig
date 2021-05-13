# Huawei Autoconfig

## What is this project?

This project was created to compose configuration files for Huawei switches fast and error-free. 
It can make it from scratch or use an existing configuration from D-Link or Huawei switch to transfer some parameters like VLANS, port descriptions, etc. 
It has GUI which is Tk-based. The project was initially developed for Windows, so to use it in Linux a couple of additional steps will be required (described below)

## How does it look like?

!["huawei_autoconfig - Initial parameters"](https://github.com/pavel-piatetskii/huawei_autoconfig/blob/master/docs/initial_parameters.png)

The first window is called "Initial parameters". If we want to compose a config file from scratch, we will need to set up network parameters as well as main VLANs names and IDs. Also, a switch model should be chosen from the list of available models.

If we would like to replace an existing switch, this can be done by clicking on the "Replacement" button and choosing a configuration file of an existing switch. The parser I wrote assumes that the config file was fetched by the RANCID differ. Then, we will need to choose the model with which the existing switch should be replaced. 


!["huawei_autoconfig - Main window"](https://github.com/pavel-piatetskii/huawei_autoconfig/blob/master/docs/main_window.png)
After pressing the Next button, the Main application window appears. It already has some parameters filled, so all we need to do is to add descriptions, VLANs, or other things we need. 

Features of the Main window:
- Ports can be massively activated/deactivated by clicking on the "Active" column header by left/right mouse button correspondingly;
- The same is actual for the "PPPoE only" column header;
- VLANs can be added or deleted in the "List of VLANs" section;
- Settings button allows to choose default folders for switch configuration template files and composed configurations;

To save the configuration file with entered data, click the "Create config" button. After that, you will be asked to choose a name and the path to save the config file. By default, the name is the same as a System name and the path is the folder from the settings, mentioned above.

## How to launch the application?

### Windows
Just type this command in the project folder in the Command Shell:
`python3 ./huawei_autoconfig_rep.py`

### Ubuntu
You will need to install the tkinter GUI library first.

```sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3-tk
```
Then type this command in the project folder:
`python3 huawei_autoconfig_rep.py`
