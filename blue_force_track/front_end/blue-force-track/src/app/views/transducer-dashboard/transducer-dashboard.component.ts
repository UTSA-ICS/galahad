import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-transducer-dashboard',
  templateUrl: './transducer-dashboard.component.html',
  styleUrls: ['./transducer-dashboard.component.css']
})
export class TransducerDashboardComponent implements OnInit {

  // Table Config
  cols = [
    { field: 'dn', header: 'Domain Name' },
    { field: 'name', header: 'Username' },
    { field: 'ou', header: 'Organizational Unit' },
    { field: 'cstartEnabled', header: 'Organizational Unit' },
    { field: 'ctype', header: 'Organizational Unit' },
    { field: 'cid', header: 'Id' }
  ];

  tableData: any[];

  constructor() { }

  ngOnInit() {
    this.tableData = [
      {
        dn: 'cusername=fpatwa,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com',
        ou: 'virtue',
        cid: 'path_mkdir',
        name: 'Directory Creation',
        cstartEnabled: 'RUNNING',
        ctype: 'SecurityTestRole1539876260',
        crecAccess: [],
        cstartConfig: '{}'
      }
    ];
  }

}
