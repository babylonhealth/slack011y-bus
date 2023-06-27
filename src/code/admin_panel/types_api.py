from flask import abort
from flask_restx import Namespace
from flask_restx import Resource
from flask_restx import fields
from varname import nameof

from src.code.admin_panel.helper import HelperResource
from src.code.model.control_panel import ControlPanel
from src.code.model.schemas import ChannelProperties
from src.code.model.schemas import ChannelPropertiesFeatures
from src.code.model.schemas import channel_properties_schema
from src.code.model.schemas import types_schema

types_description = """
List and modify category types for a channel.
"""
types_ns = Namespace("types", description=types_description)

emojis_dict = types_ns.model(
    "emojisDict",
    {
        "emoji": fields.String(
            title="Emoji icon",
            description=(
                '\\U+ unicode byte sequence of an emoji to categorize a message. Use an "" (empty string) if you'
                " provide image name."
            ),
            example="U+1F198",
            required=True,
        ),
        "alias": fields.String(
            title="Another emoji name",
            description="Another emoji name that should categorize the message as the same type",
            example="sos",
            required=True,
        ),
        "image": fields.String(
            title="Image filename", description="For custom emoji, provide name of image here.", example="cloud-pr.png"
        ),
        "color": fields.String(
            title="Type color",
            description="Color for internal graphing purposes. Will be deprecated soon.",
            example="#619BFF",
        ),
        "meaning": fields.String(
            title="Type description",
            description=(
                "A short description of the type. It will be used as part of not selected emoji response, if used."
                " Accepts markdown."
            ),
            example="Need help",
            required=True,
        ),
    },
    skip_none=True,
    strict=True,
)

emojis_desc = "Contains a dict of emojis, each defining a type. Key should be the same as the emoji used."

type_dict = types_ns.model(
    "typeDict",
    {
        "not_selected_response": fields.String(
            title="Not selected response message",
            description=(
                "This text will be displayed if a message has no types in them, along with meanings of the types."
                " Accepts markdown."
            ),
            example="You haven't selected a type for your message.",
            required=True,
        ),
        "emojis": fields.Wildcard(
            fields.Nested(emojis_dict),
            required=True,
            title="Emojis dict",
            description=emojis_desc,
        ),
    },
    skip_none=True,
    strict=True,
)

type_dict_no_response = types_ns.model(
    "typeDictNoResponse",
    {
        "emojis": fields.Wildcard(
            fields.Nested(emojis_dict),
            required=True,
            title="Emojis dict",
            description=emojis_desc,
        ),
    },
    skip_none=True,
    strict=True,
)

types_desc = "Contains the emoji types and not_selected_response."

type_dict_json = types_ns.model(
    "typeDictJson",
    {
        "enabled": fields.Boolean(
            title="Feature flag", description="Controls if feature is enabled or not", example=True
        ),
        "types": fields.Nested(
            type_dict,
            required=True,
            title="Types dict",
            description=types_desc,
        ),
    },
    strict=True,
)

type_dict_json_no_enabled = types_ns.model(
    "typeDictJsonNoEnabled",
    {
        "types": fields.Nested(
            type_dict,
            required=True,
            title="Types dict",
            description=types_desc,
        ),
    },
    strict=True,
)

type_dict_json_no_enabled_no_response = types_ns.model(
    "typeDictJsonNoEnabledNoResponse",
    {
        "types": fields.Nested(
            type_dict_no_response,
            required=True,
            title="Types dict",
            description="Contains the emoji types.",
        ),
    },
    strict=True,
)

type_delete = types_ns.model(
    "typeDelete",
    model={
        "emoji_to_delete": fields.List(fields.String(example="cloud-help", min_length=1), required=True, min_items=1)
    },
    strict=True,
)

no_type_selected_response = types_ns.model(
    "notSelectedResponse",
    {
        "not_selected_response": fields.String(
            title="No type selected response",
            description=(
                "This text will be displayed if a message has no types in them, along with meanings of the types."
                " Accepts markdown."
            ),
            example="You haven't selected a type for your message.",
        )
    },
    strict=True,
)


@types_ns.route("/")
class TypesResource(Resource):
    @types_ns.doc(description="List existing types and feature status.")
    @types_ns.response(code=200, description="List of types for a channel", model=type_dict_json)
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def get(self, channel_id):
        channel_properties: ChannelProperties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        return channel_properties.get_feature_status_dict("types"), 200

    @types_ns.doc(description="Add new types. Existing ids will throw error - delete first.")
    @types_ns.expect(type_dict_json_no_enabled_no_response, validate=True)
    @types_ns.response(code=200, description="Types added. Current feature status", model=type_dict_json)
    @types_ns.response(code=400, description="Bad input")
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def put(self, channel_id):
        body = types_ns.payload
        channel_properties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        for type_spec in body["types"]["emojis"]:
            if type_spec in channel_properties._types.emojis:
                abort(409, description=f"{type_spec} already exists. Delete first")
        for type_spec in body["types"]["emojis"]:
            channel_properties._types.emojis[type_spec] = body["types"]["emojis"][type_spec]
        try:
            ControlPanel().update_channel_property(channel_id, "_types", types_schema.dump(channel_properties._types))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200

    @types_ns.doc(description="Delete existing types.")
    @types_ns.expect(type_delete, validate=True)
    @types_ns.response(code=200, description="Types deleted. Current feature status", model=type_dict_json)
    @types_ns.response(code=400, description="Bad input")
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def delete(self, channel_id):
        body = types_ns.payload["emoji_to_delete"]
        channel_properties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        for type_id in body:
            if type_id not in channel_properties._types.emojis:
                abort(404, description=f"{type_id} not found in existing types")
        for type_id in body:
            del channel_properties._types.emojis[type_id]
        try:
            ControlPanel().update_channel_property(channel_id, "_types", types_schema.dump(channel_properties._types))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200

    @types_ns.doc(description="Replace existing types.")
    @types_ns.expect(type_dict_json_no_enabled, validate=True)
    @types_ns.response(code=200, description="Types replaced. Current feature status", model=type_dict_json)
    @types_ns.response(code=400, description="Bad input")
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def post(self, channel_id):
        channel_properties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        channel_properties._types.emojis = types_ns.payload["types"]["emojis"]
        channel_properties._types.not_selected_response = types_ns.payload["types"]["not_selected_response"]
        try:
            ControlPanel().update_channel_property(channel_id, "_types", types_schema.dump(channel_properties._types))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200


@types_ns.route("/no_type_selected")
class NoTypeSelectedResource(Resource):
    @types_ns.doc(description="Replace existing no type selected response.")
    @types_ns.expect(no_type_selected_response, validate=True)
    @types_ns.response(code=200, description="Response modified. Current feature status.", model=type_dict_json)
    @types_ns.response(code=400, description="Bad input")
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def post(self, channel_id):
        channel_properties: ChannelProperties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        channel_properties._types.not_selected_response = types_ns.payload["not_selected_response"]
        try:
            ControlPanel().update_channel_property(channel_id, "_types", types_schema.dump(channel_properties._types))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200

    @types_ns.doc(description="Delete existing no type selected response.")
    @types_ns.response(code=200, description="Response modified. Current feature status.", model=type_dict_json)
    @types_ns.response(code=400, description="Bad input")
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def delete(self, channel_id):
        channel_properties: ChannelProperties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        channel_properties._types.not_selected_response = ""
        try:
            ControlPanel().update_channel_property(channel_id, "_types", types_schema.dump(channel_properties._types))
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200


@types_ns.route("/enable")
class TypesEnableResource(Resource):
    @types_ns.doc(description="Enable types feature.")
    @types_ns.response(code=200, description="Current feature status", model=type_dict_json)
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        channel_properties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        channel_properties.features.types.enabled = True
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.types), True)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200


@types_ns.route("/disable")
class TypesDisableResource(Resource):
    @types_ns.doc(description="Disable types feature.")
    @types_ns.response(code=200, description="Current feature status", model=type_dict_json)
    @types_ns.response(code=404, description="Channel not found")
    @types_ns.response(code=500, description="Internal server error")
    def put(self, channel_id: str):
        channel_properties = channel_properties_schema.load(
            data=HelperResource.get_control_panel_or_404(channel_id).channel_properties
        )
        channel_properties.features.types.enabled = False
        try:
            ControlPanel().toggle_feature(channel_id, nameof(ChannelPropertiesFeatures.types), False)
        except Exception:
            abort(500, description="Had a problem updating database. See server logs.")
        return channel_properties.get_feature_status_dict("types"), 200
