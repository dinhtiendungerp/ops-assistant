/// <summary>
/// Dang ky codeunit "NWV Replen. Service" thanh ODataV4 web service `NWVReplenService` khi cai hoac nang cap app.
/// Goi: POST .../ODataV4/NWVReplenService_ReadTable?company=NWV
/// </summary>
codeunit 70276 "NWV Replen. Service Install"
{
    Subtype = Install;

    trigger OnInstallAppPerCompany()
    begin
        Register();
    end;

    procedure Register()
    var
        TenantWebService: Record "Tenant Web Service";
        WebServiceManagement: Codeunit "Web Service Management";
    begin
        WebServiceManagement.CreateTenantWebService(
            TenantWebService."Object Type"::Codeunit, Codeunit::"NWV Replen. Service", 'NWVReplenService', true);
        WebServiceManagement.CreateTenantWebService(
            TenantWebService."Object Type"::Codeunit, Codeunit::"NWV Agent Calc Service", 'NWVAgentCalcService', true);
    end;
}

codeunit 70277 "NWV Replen. Service Upgrade"
{
    Subtype = Upgrade;

    trigger OnUpgradePerCompany()
    var
        Install: Codeunit "NWV Replen. Service Install";
    begin
        Install.Register();
    end;
}
