f0cal farm device-type query
f0cal farm image query
f0cal farm device-type query "manufacturer==NVidia"
f0cal farm image query "vendor==Canonical"
f0cal farm config update "api_key=${API_KEY}"
f0cal farm config update "api_url=https://staging.f0cal.com/api"
f0cal farm instance create ${INSTANCE_NAME} --device-type ${DEVICE_TYPE}  --image ${IMAGE} --wait
f0cal farm instance query "status==running"
f0cal farm instance stop ${INSTANCE_NAME}
f0cal farm instance update ${INSTANCE_NAME} "name=foo"
