def set_v4_ips_for_domain(c, domain, ips):
    """
    Creates or updates the domain name with A records of the IPs.
    """
    session = c["session"]
    r53_client = session.client('route53')

    my_zone = None
    for zone in r53_client.list_hosted_zones()['HostedZones']:
        if "aca-aws.s.uw.edu." == zone["Name"]:
            my_zone = zone

    zone_id = my_zone["Id"].replace('/hostedzone/', '')

    records = []
    for ip in ips:
        records.append({"Value": ip})

    data = {"Comment": "ACA-AWS Automation",
            "Changes": [{"Action": "UPSERT",
                         "ResourceRecordSet": {"Name": domain,
                                               "Type": "A",
                                               "TTL": 10,
                                               "ResourceRecords": records
                                               }
                         }
                        ]
            }

    response = r53_client.change_resource_record_sets(HostedZoneId=zone_id,
                                                      ChangeBatch=data)

    waiter = r53_client.get_waiter('resource_record_sets_changed')
    waiter.wait(Id=response["ChangeInfo"]["Id"])
