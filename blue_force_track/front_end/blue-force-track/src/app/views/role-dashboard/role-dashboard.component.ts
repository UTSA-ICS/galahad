import { Component, OnInit, OnDestroy } from '@angular/core';
import {Role} from '../../models/Role';
import {DataService} from '../../services/data.service';
import { interval } from 'rxjs/index';

@Component({
  selector: 'app-role-dashboard',
  templateUrl: './role-dashboard.component.html',
  styleUrls: ['./role-dashboard.component.css']
})
export class RoleDashboardComponent implements OnInit, OnDestroy {

  // Bar chat config
  barData: any[];
  barView: any[] = [700, 400];

  // options
  barShowXAxis = true;
  barShowYAxis = true;
  barGradient = false;
  barShowLegend = true;
  barShowXAxisLabel = true;
  barXAxisLabel = 'Role';
  barShowYAxisLabel = true;
  barYAxisLabel = '# Virtues';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'cid', header: 'Id'},
    { field: 'name', header: 'Role Name' },
    { field: 'cstate', header: 'State' },
    { field: 'cversion', header: 'Version' }
  ];

  tableData: Role[];

  private alive: boolean;

  constructor(private dataService: DataService) {
    this.alive = true;
  }

  ngOnInit() {
    this.dataService.getVirtuesPerRole().subscribe(
      response => this.barData = this.buildBarData(response)
    );

    this.dataService.getRoles().subscribe(
      roles => (
        this.tableData = this.parseArrays(roles)));

    // Refresh every 10 seconds
    const secondsCounter = interval(10000);
    secondsCounter.subscribe(n =>
      this.dataService.getVirtuesPerRole().subscribe(
        response => this.barData = this.buildBarData(response)
      )
    );
    secondsCounter.subscribe(n =>
      this.dataService.getRoles().subscribe(
        roles => (
          this.tableData = this.parseArrays(roles)))
    );

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

  private parseArrays(roles: Role[]): Role[] {
    for (const role of roles) {
      try {
        let appIds = role.cappIds as any;
        appIds = (appIds as string).replace(/u\'/g, '\'');
        role.cappIds = JSON.parse((appIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        role.cappIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        let resIds = role.cstartResIds as any;
        resIds = (resIds as string).replace(/u\'/g, '\'');
        role.cstartResIds = JSON.parse((resIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        role.cstartResIds = ['ERROR_PROCESSING_JSON'];
      }
      try {
        let transIds = role.cstartTransIds as any;
        transIds = (transIds as string).replace(/u\'/g, '\'');
        role.cstartTransIds = JSON.parse((transIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        role.cstartTransIds = ['ERROR_PROCESSING_JSON'];
      }
    }
    return roles;
  }

  ngOnDestroy() {
    this.alive = false;
  }

}
