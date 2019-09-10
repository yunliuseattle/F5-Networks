# coding=utf-8
#
# Copyright 2015-2019 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# usage: runtime_calc.py [-h] host username rule

########################################################
# Imports
########################################################

from f5.bigip import ManagementRoot
from xlsxwriter.utility import xl_range
import argparse
import getpass
import platform
import requests
import time
import xlsxwriter


# Disable cert warnings for lab gear
requests.packages.urllib3.disable_warnings()

########################################################
# Build CLI options arguments
########################################################

# Create parser
parser = argparse.ArgumentParser()
parser.add_argument('host', nargs=1)
parser.add_argument('username', nargs=1)
parser.add_argument('rule', nargs=1)
args = parser.parse_args()

########################################################
# Get the iRule and its stats from BIG-IP
########################################################

# Ask user for password
pw = getpass.getpass(prompt='\n\tWell hello {}, please enter your password: '.format(args.username[0]))

# Connect to BIG-IP
obj = ManagementRoot(args.host[0], args.username[0], pw)

# Grab the iRule
r1 = args.rule[0]
r = obj.tm.ltm.rules.rule.load(name=r1)

# Grab the iRule stats
rstats = r.stats.load()

########################################################
# Get the Processor core count and speed
########################################################

# Selflinks for cpu cores/speed, stats are deep nested
hw_sub1 = 'https://localhost/mgmt/tm/sys/hardware/hardware-version'
hw_sub2 = 'https://localhost/mgmt/tm/sys/hardware/hardware-version/cpus'
hw_sub3 = 'https://localhost/mgmt/tm/sys/hardware/hardwareVersion/cpus/versions'
hw_sub4_cores = 'https://localhost/mgmt/tm/sys/hardware/hardwareVersion/cpus/versions/1'
hw_sub4_speed = 'https://localhost/mgmt/tm/sys/hardware/hardwareVersion/cpus/versions/2'

# Grab the hardware info from BIG-IP
hw = obj.tm.sys.hardware.load()

# Store the BIG-IP version for worksheet header
bigip_version = hw.selfLink.split('ver=')[1]

# Grab the processor MHz value recorded for the processor
cpu_MHz = hw.entries\
    .get(hw_sub1).get('nestedStats').get('entries')\
    .get(hw_sub2).get('nestedStats').get('entries')\
    .get(hw_sub3).get('nestedStats').get('entries')\
    .get(hw_sub4_speed).get('nestedStats').get('entries')\
    ['version']['description']

# Grab the number of cores recorded for the system
cpu_cores = hw.entries\
    .get(hw_sub1).get('nestedStats').get('entries')\
    .get(hw_sub2).get('nestedStats').get('entries')\
    .get(hw_sub3).get('nestedStats').get('entries')\
    .get(hw_sub4_cores).get('nestedStats').get('entries')\
    ['version']['description']

# The cores value has text in addition to the count, isolate and store
cpu_cores = cpu_cores.split(' ')[0]

# Calculate the total CPU speed in Hz, not MHz
cpu_speed = float(cpu_MHz) * int(cpu_cores) * 1000000

########################################################
# Create the Excel workbook
########################################################

# Get the current time
timestr = time.strftime("%Y%m%d-%H%M%S")

# Name the workbook iRuleRuntimeCalculator__<rulename>__<timestamp>
fname = 'iRulesRuntimeCalculator__{}__{}.xlsx'.format(r.name, timestr)
workbook = xlsxwriter.Workbook(fname)

# Set the initial Excel window size
workbook.set_size(1500,1200)

########################################################
# Cell Formatting Information
########################################################

# iRule textbox formatting
textbox_options = {
    'width': 1200,
    'height': 1400,
    'font': { 'color': 'white', 'size': 16 },
    'align': { 'vertical': 'top' },
    'gradient': { 'colors': ['#00205f', '#84358e'] }
}

# Title Block formatting
title_format = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
})
title_format.set_font_size(20)
title_format.set_font_color('white')
title_format.set_bg_color('#00205f')

# Section Header Formatting
secthdr_format = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
})
secthdr_format.set_font_size(16)
secthdr_format.set_font_color('white')
secthdr_format.set_bg_color('#00205f')

# Table Data Formatting - BOLD for headers and total
tabledata_format = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
})
tabledata_format.set_font_size(14)

# Table Data Formatting - ints for rule data max requests
tabledata2_format = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
    'num_format': '0',
})
tabledata2_format.set_font_size(14)

# Table Data Formatting - percentages for rule data
tabledata3_format = workbook.add_format({
    'bold': 1,
    'border': 1,
    'align': 'center',
    'valign': 'vcenter',
    'num_format': '0.0000000000000%',
})
tabledata3_format.set_font_size(14)



########################################################
# Create worksheet one for stats, two for iRule contents
########################################################

worksheet1 = workbook.add_worksheet('iRule Stats')
worksheet2 = workbook.add_worksheet('iRule Contents')

########################################################
# Generate iRule stats worksheet data
########################################################

worksheet1.set_column(1, 1, 30)
worksheet1.set_column(2, 2, 15)
worksheet1.set_column(3, 5, 25)
worksheet1.merge_range('B2:F2', 'iRules Runtime Calculator - {}'.format(r.name), title_format)
worksheet1.write_string(4, 1, 'BIG-IP version: {}, OS version: {} {}, '
                              'Python version: {}'.format(bigip_version,
                                                          platform.system(),
                                                          platform.release(),
                                                          platform.python_version()))
worksheet1.write_string(5, 1, 'For more details, see article "Intermediate iRules: '
                              'Evaluating Performance" on DevCentral:')
worksheet1.write_string(6, 1, 'https://devcentral.f5.com/s/articles/intermediate-irules-evaluating-performance-20433')
worksheet1.write_string(8, 1, 'Cycles/Sec', tabledata_format)
worksheet1.write_number(8, 3, cpu_speed, tabledata_format)

# Write the iRule data into the user data table
worksheet1.merge_range('B11:F11', 'Runtime / Request (cycles)', secthdr_format)
worksheet1.write_row(11, 1, ('Event Name', '# of Requests', 'MIN', 'AVG', 'MAX'), tabledata_format)

rowval = 12
event_list = []
for sl in rstats.entries:
    raw_data = rstats.entries.get(sl).get('nestedStats').get('entries')
    event_name = raw_data['eventType']['description']
    event_list.append(event_name)
    executions = raw_data['totalExecutions']['value']
    min_cycles = raw_data['minCycles']['value']
    avg_cycles = raw_data['avgCycles']['value']
    max_cycles = raw_data['maxCycles']['value']
    worksheet1.write_row(rowval, 1, (str(event_name), int(executions), int(min_cycles), int(avg_cycles),
                                     int(max_cycles)), tabledata_format)
    rowval += 1

worksheet1.write_string(rowval, 1, 'Total', tabledata_format)
worksheet1.write_formula(rowval, 2, '=MAX({})'.format(xl_range(12,2,rowval-1,2)), tabledata_format)
worksheet1.write_formula(rowval, 3, '=SUM({})'.format(xl_range(12,3,rowval-1,3)), tabledata_format)
worksheet1.write_formula(rowval, 4, '=SUM({})'.format(xl_range(12,4,rowval-1,4)), tabledata_format)
worksheet1.write_formula(rowval, 5, '=SUM({})'.format(xl_range(12,5,rowval-1,5)), tabledata_format)

# increment rowval to start first analysis table
rowval += 3

# Populate the run time /request (microseconds) table based on the rule stats
worksheet1.merge_range('B{0}:F{0}'.format(rowval), 'Runtime / Request (microseconds)', secthdr_format)
worksheet1.write_row(rowval, 1, ('Event Name', '# of Requests', 'MIN', 'AVG', 'MAX'), tabledata_format)
rowval += 1
for event in event_list:
    worksheet1.write_string(rowval, 1, event, tabledata_format)
    worksheet1.write_formula(rowval, 2, '=C{}'.format(rowval - (3 + len(event_list))), tabledata_format)
    worksheet1.write_formula(rowval, 3, '=D{}*1000000/$D$9'.format(rowval - (3 + len(event_list))), tabledata_format)
    worksheet1.write_formula(rowval, 4, '=E{}*1000000/$D$9'.format(rowval - (3 + len(event_list))), tabledata_format)
    worksheet1.write_formula(rowval, 5, '=F{}*1000000/$D$9'.format(rowval - (3 + len(event_list))), tabledata_format)
    rowval += 1

worksheet1.write_string(rowval, 1, 'Total', tabledata_format)
worksheet1.write_formula(rowval, 2, '=MAX({})'.format(xl_range(rowval-len(event_list),2,rowval-1,2)), tabledata_format)
worksheet1.write_formula(rowval, 3, '=SUM({})'.format(xl_range(rowval-len(event_list),3,rowval-1,3)), tabledata_format)
worksheet1.write_formula(rowval, 4, '=SUM({})'.format(xl_range(rowval-len(event_list),4,rowval-1,4)), tabledata_format)
worksheet1.write_formula(rowval, 5, '=SUM({})'.format(xl_range(rowval-len(event_list),5,rowval-1,5)), tabledata_format)

# increment rowval again to start second analysis table
rowval += 3

# Populate the % CPU utilization /request table based on the rule stats
worksheet1.merge_range('B{0}:F{0}'.format(rowval), 'CPU Utilization / Request (percent)', secthdr_format)
worksheet1.write_row(rowval, 1, ('Event Name', '# of Requests', 'MIN', 'AVG', 'MAX'), tabledata_format)
rowval += 1
for event in event_list:
    worksheet1.write_string(rowval, 1, event, tabledata_format)
    worksheet1.write_formula(rowval, 2, '=C{}'.format(rowval - 1 - (6 + 2*len(event_list))), tabledata_format)
    worksheet1.write_formula(rowval, 3, '=D{}/$D$9'.format(rowval - 1 - (6 + 2*len(event_list))), tabledata3_format)
    worksheet1.write_formula(rowval, 4, '=E{}/$D$9'.format(rowval - 1 - (6 + 2*len(event_list))), tabledata3_format)
    worksheet1.write_formula(rowval, 5, '=F{}/$D$9'.format(rowval - 1 - (6 + 2*len(event_list))), tabledata3_format)
    rowval += 1

worksheet1.write_string(rowval, 1, 'Total', tabledata_format)
worksheet1.write_formula(rowval, 2, '=MAX({})'.format(xl_range(rowval-len(event_list),2,rowval-1,2)), tabledata_format)
worksheet1.write_formula(rowval, 3, '=SUM({})'.format(xl_range(rowval-len(event_list),3,rowval-1,3)), tabledata3_format)
worksheet1.write_formula(rowval, 4, '=SUM({})'.format(xl_range(rowval-len(event_list),4,rowval-1,4)), tabledata3_format)
worksheet1.write_formula(rowval, 5, '=SUM({})'.format(xl_range(rowval-len(event_list),5,rowval-1,5)), tabledata3_format)

# increment rowval again to start third analysis table
rowval += 3

# Populate the Max # of requests table based on the rule stats
worksheet1.merge_range('B{0}:F{0}'.format(rowval), 'Max Requests', secthdr_format)
worksheet1.write_row(rowval, 1, ('Event Name', '# of Requests', 'MIN', 'AVG', 'MAX'), tabledata_format)
rowval += 1
for event in event_list:
    worksheet1.write_string(rowval, 1, event, tabledata_format)
    worksheet1.write_formula(rowval, 2, '=C{}'.format(rowval - (3 + len(event_list))), tabledata_format)
    worksheet1.write_formula(rowval, 3, '=1/D{}'.format(rowval - (3 + len(event_list))), tabledata2_format)
    worksheet1.write_formula(rowval, 4, '=1/E{}'.format(rowval - (3 + len(event_list))), tabledata2_format)
    worksheet1.write_formula(rowval, 5, '=1/F{}'.format(rowval - (3 + len(event_list))), tabledata2_format)
    rowval += 1

worksheet1.write_string(rowval, 1, 'Total', tabledata_format)
worksheet1.write_formula(rowval, 2, '=MAX({})'.format(xl_range(rowval-len(event_list),2,rowval-1,2)), tabledata_format)
worksheet1.write_formula(rowval, 3, '=1/D{}'.format(rowval - (3 + len(event_list))), tabledata2_format)
worksheet1.write_formula(rowval, 4, '=1/E{}'.format(rowval - (3 + len(event_list))), tabledata2_format)
worksheet1.write_formula(rowval, 5, '=1/F{}'.format(rowval - (3 + len(event_list))), tabledata2_format)

########################################################
# Generate iRule contents worksheet data
########################################################

worksheet2.insert_textbox('B2', r.apiAnonymous, textbox_options)

########################################################
# Finish up!
########################################################

print('\n\n\tHoly iRule perfomance analysis, Batman! Your mission file is {}\n\n'.format(fname))
# Close the workbook
workbook.close()