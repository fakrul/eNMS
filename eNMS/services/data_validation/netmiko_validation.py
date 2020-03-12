from sqlalchemy import Boolean, Float, ForeignKey, Integer
from traceback import format_exc

from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.fields import BooleanField, HiddenField, StringField
from eNMS.forms.automation import NetmikoForm
from eNMS.models.automation import ConnectionService


class NetmikoValidationService(ConnectionService):

    __tablename__ = "netmiko_validation_service"
    pretty_name = "Netmiko Validation"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    enable_mode = Column(Boolean, default=True)
    config_mode = Column(Boolean, default=False)
    command = Column(LargeString)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Float, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)
    expect_string = Column(SmallString)
    auto_find_prompt = Column(Boolean, default=True)
    strip_prompt = Column(Boolean, default=True)
    strip_command = Column(Boolean, default=True)
    use_genie = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "netmiko_validation_service"}

    def job(self, run, device):
        netmiko_connection = run.netmiko_connection(self, device)
        command = run.sub(self.command, locals())
        run.log("info", f"Sending '{command}' with Netmiko", device, self)
        expect_string = run.sub(self.expect_string, locals())
        netmiko_connection.session_log.truncate(0)
        try:
            result = netmiko_connection.send_command(
                command,
                delay_factor=self.delay_factor,
                expect_string=expect_string or None,
                auto_find_prompt=self.auto_find_prompt,
                strip_prompt=self.strip_prompt,
                strip_command=self.strip_command,
                use_genie=self.use_genie,
            )
        except Exception:
            return {
                "command": command,
                "error": format_exc(),
                "result": netmiko_connection.session_log.getvalue().decode(),
                "success": False,
            }
        return {"command": command, "result": result}


class NetmikoValidationForm(NetmikoForm):
    form_type = HiddenField(default="netmiko_validation_service")
    command = StringField(substitution=True)
    expect_string = StringField(substitution=True)
    auto_find_prompt = BooleanField(default=True)
    strip_prompt = BooleanField(default=True)
    strip_command = BooleanField(default=True)
    use_genie = BooleanField(default=False)
    groups = {
        "Main Parameters": {"commands": ["command"], "default": "expanded"},
        "Advanced Netmiko Parameters": {
            "commands": [
                "expect_string",
                "auto_find_prompt",
                "strip_prompt",
                "strip_command",
                "use_genie",
            ],
            "default": "hidden",
        },
        **NetmikoForm.groups,
    }
