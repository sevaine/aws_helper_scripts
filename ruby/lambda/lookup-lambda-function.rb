#!/usr/bin/env ruby
require 'aws-sdk'

def lambda_function_arn(name)
  lambda = Aws::Lambda::Client.new(region: ENV.fetch('AWS_REGION', 'ap-southeast-2'))
  next_marker = nil
  resp = lambda.list_functions()
  results = []
  while true
    break if resp.functions.empty?
    resp.functions.each do |function|
      if function.function_name.start_with?("#{name}")
        results << function
      end
    end
    next_marker = resp.next_marker
    break if next_marker.nil?
  end
  return results
end

if ARGV.length() != 2
  puts "Usage: #{$0} LAMBDA_NAME LAMBDA_SLICE"
  exit
end

function_name = ARGV[1]

puts lambda_function_arn(function_name)

