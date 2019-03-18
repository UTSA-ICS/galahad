export class User {
  private _dn: string;
  private _objectClass: string;
  private _ou: string;
  private _cusername: string;
  private _cauthRoleIds: string[];


  constructor() {
  }


  get dn(): string {
    return this._dn;
  }

  set dn(value: string) {
    this._dn = value;
  }

  get objectClass(): string {
    return this._objectClass;
  }

  set objectClass(value: string) {
    this._objectClass = value;
  }

  get ou(): string {
    return this._ou;
  }

  set ou(value: string) {
    this._ou = value;
  }

  get cusername(): string {
    return this._cusername;
  }

  set cusername(value: string) {
    this._cusername = value;
  }

  get cauthRoleIds(): string[] {
    return this._cauthRoleIds;
  }

  set cauthRoleIds(value: string[]) {
    this._cauthRoleIds = value;
  }
}
