//*************************************************************
//      Netfilter Module for blocking network access          *
//							      *
//	Copyright (c) 2018 by Raytheon BBN Technologies Corp. *
//							      *
//*************************************************************



#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/kthread.h>
#include "map.h"

//netfilter hook options
static struct nf_hook_ops nfho_in;
static struct nf_hook_ops nfho_out;

//Unix Domain Socket Kernel Thread
static struct task_struct *uds_thread;
static const char UDS_THREAD_NAME[14] = "portblock_uds";

struct packetRules {
	//Struct for holding different types of rules
	map_int_t in_ports;
	map_int_t out_ports;
	map_int_t in_ip;
	map_int_t out_ip;
};

static struct packetRules rules;


//Unix Domain Socket Thread
//Responsible for receiving actuator commands
int uds_func(void *data){

	while(!kthread_should_stop()){
		printk(KERN_INFO "Running UDS thread...");
		msleep(15000);
		//Test: Remove IP address block
		map_remove(&rules.in_ip, "216.58.219.206");
	}

	return 0;
}


//Incoming packets hook
unsigned int port_blocker_in_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	uint16_t dst_port;
	uint16_t src_port;

	char ip_src[16];
	char ip_dst[16];
	int* val;

	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ip_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}

	//retrieve source and destination addresses for the packet
	//Convert Source IP Decimal into IPv4 string
	snprintf(ip_src, 16, "%pI4", &ip_header->saddr);

	//Convert Destination IP Decimal into IPv4 string
	snprintf(ip_dst, 16, "%pI4", &ip_header->daddr);


	val = map_get(&rules.in_ip, ip_src);
	if(val != NULL){
		//drop traffic
		*val = *val + 1;
		printk(KERN_INFO "Blocking IP Address from %s\n", ip_src);
		return NF_DROP;
	}


	if (ip_header->protocol == IPPROTO_TCP){


		tcp_header = (struct tcphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!tcp_header){
			return NF_ACCEPT;
		}

		printk(KERN_INFO "Incoming TCP packet\n");

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);


		printk(KERN_INFO "Source Port: %d\n", src_port);
		printk(KERN_INFO "Dest port: %d\n", dst_port);

		//test for blocking all traffic incoming on port 80
		if(dst_port == 80){
			printk(KERN_INFO "dropping all port 80 packets\n");
			return NF_DROP;
		}
	}

	return NF_ACCEPT;
}


//Outgoing packets hook
unsigned int port_blocker_out_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	uint16_t dst_port;
	uint16_t src_port;

	char ip_src[16];
	char ip_dst[16];
	char sport[6];
	int* val;

	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ip_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}

	//retrieve source and destination addresses for the packet
	//Convert Source IP Decimal into IPv4 string
	snprintf(ip_src, 16, "%pI4", &ip_header->saddr);

	//Convert Destination IP Decimal into IPv4 string
	snprintf(ip_dst, 16, "%pI4", &ip_header->daddr);


	if (ip_header->protocol == IPPROTO_TCP){


		tcp_header = (struct tcphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!tcp_header){
			return NF_ACCEPT;
		}

		printk(KERN_INFO "Outgoing TCP packet\n");

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);
		snprintf(sport, 6, "%d", src_port);
		val = map_get(&rules.out_ports, sport);

		printk(KERN_INFO "Source Port: %d\n", src_port);
		printk(KERN_INFO "Dest port: %d\n", dst_port);

		if(val != NULL){
			printk(KERN_INFO "Block outgoing traffic on port %d\n", src_port);
			return NF_DROP;
		}



	}

	return NF_ACCEPT;
}


//Called when the module is loaded
int init_module(){

	printk(KERN_INFO "Loading port blocker module");
	//Set up Netfilter hook
	nfho_in.hook = port_blocker_in_hook;
	nfho_in.hooknum = NF_INET_LOCAL_IN;
	nfho_in.pf = PF_INET;
	nfho_in.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_in);

	nfho_out.hook = port_blocker_out_hook;
	nfho_out.hooknum = NF_INET_LOCAL_OUT;
	nfho_out.pf = PF_INET;
	nfho_out.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_out);

	//start Unix Domain Socket thread
	uds_thread = kthread_run(uds_func, NULL, UDS_THREAD_NAME);

	//initialize hashmaps
	map_init(&rules.in_ports);
	map_init(&rules.out_ports);
	map_init(&rules.in_ip);
	map_init(&rules.out_ip);

	//set up initial rules
	//Test: Block all incoming traffic to ports 80 and 8080
	map_set(&rules.in_ports, "80", 0);
	map_set(&rules.in_ports, "8080", 0);

	//Test: Block all incoming traffic from this Google Server
	map_set(&rules.in_ip, "216.58.219.206", 0);

	//Test: Block all outgoing traffic from port 4444
	map_set(&rules.out_ports, "4444", 0);

	
	return 0;
}


//Called when the module is removed/unloaded
void cleanup_module(){
	kthread_stop(uds_thread);
	map_deinit(&rules.in_ports);
	map_deinit(&rules.out_ports);
	map_deinit(&rules.in_ip);
	map_deinit(&rules.out_ip);
	nf_unregister_net_hook(&init_net, &nfho_in);
	nf_unregister_net_hook(&init_net, &nfho_out);
}

