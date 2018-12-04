import { Component, OnInit } from '@angular/core';
import {User} from '../../models/User';
import {DataService} from '../../services/data.service';

@Component({
  selector: 'app-user-dashboard',
  templateUrl: './user-dashboard.component.html',
  styleUrls: ['./user-dashboard.component.css']
})
export class UserDashboardComponent implements OnInit {

  // Bar chat config
  barData: any[];
  barView: any[] = [700, 400];

  // options
  barShowXAxis = true;
  barShowYAxis = true;
  barGradient = false;
  barShowLegend = true;
  barShowXAxisLabel = true;
  barXAxisLabel = 'Valor';
  barShowYAxisLabel = true;
  barYAxisLabel = 'Virtues';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'cusername', header: 'Username' },
    { field: 'ou', header: 'Organizational Unit' }
  ];

  tableData: User[];

  constructor(private dataService: DataService) { }

  ngOnInit() {

    this.dataService.getVirtuesPerRole().subscribe(
      response => (
        this.barData = this.buildBarData(response)
      ));

    this.dataService.getUsers().subscribe(
      users => (
         this.tableData = this.parseArrays(users)
      ));

    this.barData = [
      {
        name: 'Admin',
        value: 4
      }
    ];
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

  private parseArrays(users: User[]): User[] {
    for (const user of users) {
      try {
        const roleIds = user.cauthRoleIds as any;
        user.cauthRoleIds = JSON.parse((roleIds as string).replace(/\'/g, '\"'));
      } catch (e) {
        console.log(e);
        user.cauthRoleIds = ['ERROR_PROCESSING_JSON'];
      }
    }
    return users;
  }
}
