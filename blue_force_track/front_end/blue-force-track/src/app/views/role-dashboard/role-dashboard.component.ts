import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-role-dashboard',
  templateUrl: './role-dashboard.component.html',
  styleUrls: ['./role-dashboard.component.css']
})
export class RoleDashboardComponent implements OnInit {

  // Table Config
  cols = [
    { field: 'dn', header: 'Domain Name' },
    { field: 'ou', header: 'Organizational Unit' },
    { field: 'name', header: 'Role Name' },
    { field: 'cstate', header: 'State' },
    { field: 'version', header: 'Version' },
    { field: 'cid', header: 'Id'}
  ];

  tableData: any[];

  constructor() { }

  ngOnInit() {
    this.tableData = [
      {
        dn: 'cusername=fpatwa,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com',
        ou: 'virtue',
        cid: 'Virtue_SecurityTestRole_1539878119',
        name: 'TestRole',
        cstate: 'CREATED',
        version: '1.0',
        cappIds: [],
        cresIds: [],
        ctransIds: []
      }
    ];
  }
}
