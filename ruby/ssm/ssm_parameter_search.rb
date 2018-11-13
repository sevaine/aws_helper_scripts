#!/usr/bin/env ruby
require 'aws-sdk'
region = ENV.fetch('AWS_REGION','ap-southeast-2')
pattern = ARGV[0]

if pattern.nil?
  puts "Usage: #{$0} MATCH_PATTERN"
  exit
end

puts "looking for pattern #{pattern}"

SSM = Aws::SSM::Client.new(region: region)

def get_parameters_by_path(path, next_token = nil)
  params = {
    path: path,
    max_results: 10,
    recursive: true,
    with_decryption: false
  }
  params[:next_token] = next_token unless next_token.nil?
  SSM.get_parameters_by_path(params)
end

def parameters_by_path(path, pattern)
  next_token = nil
  while true
    resp = get_parameters_by_path(path, next_token)
    break if resp.parameters.empty?
    resp.parameters.each do |parameter|
      yield parameter
    end
    next_token = resp.next_token
    break if next_token.nil?
  end
end

parameters_by_path('/', pattern) {|x|
  param_name = x.name
  if param_name.match(pattern)
    puts param_name
  end
}
