# GLOBAL1TEL Admin Panel

## Install / upgrade

1. Back up the database.
2. Run `database/migrations/admin_panel_upgrade.sql` on the existing GLOBAL1TEL database.
3. Create an Admin account from the server shell:

   `php scripts/create-admin.php admin 'CHANGE-THIS-STRONG-PASSWORD' admin@example.com`

4. Sign in through the normal `/ints/login` page. Admin accounts are redirected to `/ints/admin/AdminDashboard`.

## Admin capabilities

- Global dashboard: all numbers, managers, agents, clients, SMS totals, OTP-event totals, ranges and pending payment requests.
- Create Manager, Agent and Client accounts with the correct hierarchy.
- Activate, suspend or delete eligible accounts.
- Global number inventory search.
- Global SMS/CDR report with Manager/Agent/Client attribution and OTP-event filtering.
- Payment request review/status controls.
- System controls including minimum withdrawal values, payment request switch, maintenance mode and default page size.

## OTP security design

The upgrade does **not** store or expose inbound SMS message bodies or verification-code values. It records only `otp_detected=1` when an inbound message looks like an OTP/verification message. This supports operational OTP statistics without creating a centralized store of authentication codes.

Existing CDR rows default to `otp_detected=0`; detection applies to newly received messages after the upgrade.
