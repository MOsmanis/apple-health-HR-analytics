from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import xmltodict
import sys
import re
import warnings
warnings.filterwarnings("ignore")

input_path = sys.argv[1]
with open(input_path, 'r') as xml_file:
    input_data = xmltodict.parse(xml_file.read())
    records_list = input_data['HealthData']['Record']
    df = pd.DataFrame(records_list)
hr_recordings = df[df['@type'] == 'HKQuantityTypeIdentifierHeartRate']
hr_recordings.loc[:, '@value'] = pd.to_numeric(hr_recordings.loc[:, '@value']) #df = df.convert_dtypes()

hr_not_null = hr_recordings[hr_recordings['@device'].notnull()]
hr_devices = sorted(set(map(lambda x: re.findall(r'.*name:(.+?),.*' ,x)[0], hr_not_null['@device'].tolist())))
hr_devices.remove('iPhone')

print("Found devices from Apple Health export:")
for i in range(len(hr_devices)) : 
    print(str(i) + " - " + hr_devices[i])
npk = int(input("Select ground truth device by typing its number:\n"))

ground_truth = hr_devices[npk]
hr_devices.remove(ground_truth)

ground_truth_recordings = hr_not_null[hr_not_null['@device'].str.contains("name:" + ground_truth)]
ground_truth_by_datetime = ground_truth_recordings.groupby('@startDate').mean()

devices_hr_by_datetime = [ground_truth_by_datetime]
devices_column_names = [ground_truth]

for device in hr_devices:
    device_recordings = hr_not_null[hr_not_null['@device'].str.contains("name:" + device)]
    device_by_datetime = device_recordings.groupby('@startDate').mean()
    devices_hr_by_datetime.append(device_by_datetime)
    devices_column_names.append(device)

hr_by_datetime = pd.concat(devices_hr_by_datetime, axis = 1, join="inner")
hr_by_datetime.columns = devices_column_names


with PdfPages(ground_truth.replace(" ", "_") + '_HR_statistics.pdf') as pdf:
    
    date_strings = sorted(set(map(lambda x: x.split(" ")[0], hr_by_datetime.index.tolist())))
    
    firstPage = plt.figure(figsize=(11.69,8.27))
    firstPage.clf()
    first_date_txt = 'First date : ' + date_strings[0]
    last_date_txt = 'Last date : ' + date_strings[-1]
    ground_truth_txt = 'Selected ground truth device : ' + ground_truth

    firstPage.text(0.5,0.8, first_date_txt, transform=firstPage.transFigure, size=24, ha="center")
    firstPage.text(0.5,0.7, last_date_txt, transform=firstPage.transFigure, size=24, ha="center")
    firstPage.text(0.5,0.6, ground_truth_txt, transform=firstPage.transFigure, size=24, ha="center")

    device_mae_loc = 0.5
    hr_with_maes = hr_by_datetime.copy()
    for device in hr_devices:
        hr_with_maes["MAE " + device]= abs(hr_with_maes[ground_truth] - hr_with_maes[device])
        mae = hr_with_maes["MAE " + device].mean()
        mae_txt = 'MAE for ' + device + ' : ' + "{:.2f}".format(mae) + ' bpm'
        firstPage.text(0.5, device_mae_loc, mae_txt, transform=firstPage.transFigure, size=24, ha="center")
        device_mae_loc -= 0.1

    pdf.savefig()
    plt.close()

    for device in hr_devices:
        hr_by_datetime.plot(x=ground_truth, y = device, kind="scatter", alpha=0.2, title = device + ' BPM compared to ' + ground_truth)
        pdf.savefig()
        plt.close()
    
    for date_string in date_strings:
        hr_on_date = hr_by_datetime.filter(regex=date_string + '.*', axis=0)
        if hr_on_date.size > 10: # filter days with insignificant data
            dayPage = plt.figure(figsize=(11.69,8.27))
            dayPage.clf()

            date_txt = 'Statistics for date : ' + date_string
            mae_txt = 'MAE on this date : ' + "{:.2f}".format(mae)

            dayPage.text(0.5,0.6, date_txt, transform=dayPage.transFigure, size=24, ha="center")

            device_mae_loc = 0.5
            hr_with_maes = hr_on_date.copy()
            for device in hr_devices:
                hr_with_maes["MAE " + device]= abs(hr_with_maes[ground_truth] - hr_with_maes[device])
                mae = hr_with_maes["MAE " + device].mean()
                mae_txt = 'MAE for ' + device + ' : ' + "{:.2f}".format(mae) + ' bpm'
                dayPage.text(0.5, device_mae_loc, mae_txt, transform=dayPage.transFigure, size=24, ha="center")
                device_mae_loc -= 0.1

            pdf.savefig()
            plt.close()

            hr_on_date.index = hr_on_date.index.map(lambda x: x.split(" ")[1])
            
            hr_on_date.plot(figsize=(10,5), alpha=0.5, style='.-', title= 'All device BPMs on ' + date_string)
            plt.xlabel("")
            pdf.savefig()
            plt.close()
            
            for device in hr_devices:
                hr_on_date.plot(x=ground_truth, y = device, kind="scatter", alpha=0.5, figsize=(10,5), title = device + ' BPM compared to ' + ground_truth + ' on ' + date_string)
                pdf.savefig()
                plt.close()
