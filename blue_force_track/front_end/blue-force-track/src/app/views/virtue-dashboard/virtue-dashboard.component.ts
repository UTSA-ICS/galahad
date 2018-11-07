import { Component, OnInit } from '@angular/core';
import {DataService} from '../../services/data.service';
import {Virtue} from '../../models/Virtue';

@Component({
  selector: 'app-virtue-dashboard',
  templateUrl: './virtue-dashboard.component.html',
  styleUrls: ['./virtue-dashboard.component.css']
})
export class VirtueDashboardComponent implements OnInit {

  // Bar chat config
  barData: any[];
  barView: any[] = [700, 400];

  // options
  barShowXAxis = true;
  barShowYAxis = true;
  barGradient = false;
  barShowLegend = true;
  barShowXAxisLabel = true;
  barXAxisLabel = 'Virtue';
  barShowYAxisLabel = true;
  barYAxisLabel = 'Migrations Today';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'dn', header: 'Domain Name' },
    { field: 'cusername', header: 'Username' },
    { field: 'ou', header: 'Organizational Unit' },
    { field: 'cipAddress', header: 'IP Address' },
    { field: 'cstate', header: 'State' },
    { field: 'croleId', header: 'Role ID' },
    { field: 'cid', header: 'Id'}
  ];

  tableData: Virtue[];

  constructor(private dataService: DataService) { }

  ngOnInit() {
    this.dataService.getMigrationsPerVirtue().subscribe(
      response => (
        this.barData = this.buildBarData(response)
      ));

    // this.barData = [
    //   {
    //     name: 'Virtue_1',
    //     value: '4'
    //   },
    //   {
    //     name: 'Virtue_2',
    //     value: '6'
    //   },
    //   {
    //     name: 'Virtue_3',
    //     value: 0
    //   },
    //   {
    //     name: 'Virtue_4',
    //     value: 31
    //   }
    // ];

    this.dataService.getVirtues().subscribe(
      virtues => (
        this.tableData = this.parseArray(virtues)));
  }

  private buildBarData(response: any): any {
    const data = [];
    for (const key in response) {
      if (response.hasOwnProperty(key)) {
        const obj = {};
        obj['name'] = key;
        obj['value'] = response[key];
        data.push(obj);
      }
    }
    return data;
  }

  private parseArray(virtues: Virtue[]): Virtue[] {
    for (let virtue: Virtue of virtues) {
      try {
        virtue.cappIds = JSON.parse(virtue.cappIds.replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.cappIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        virtue.cresIds = JSON.parse(virtue.cresIds.replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.cresIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        virtue.ctransIds = JSON.parse(virtue.ctransIds.replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        virtue.ctransIds = ['ERROR_PROCESSING_JSON'];
      }
    }
    return virtues;
  }
}
